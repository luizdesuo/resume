#!/usr/bin/env python3
"""The module contains data loading functionality."""

###############################################################################
# Imports #####################################################################
###############################################################################

from __future__ import annotations

import re
from dataclasses import dataclass, field
from random import SystemRandom

import requests
import yaml  # type: ignore
from bs4 import BeautifulSoup


###############################################################################
# Base classes ################################################################
###############################################################################


@dataclass
class Paper:
    """Container for a paper.

    Parameters
    ----------
    title : str
        Title of the paper.
    url : str
        Publisher url of the paper.
    journal : str
        Journal of the paper.
    year : str
        Year in which the paper was published.
    """

    title: str = field()
    url: str = field()
    journal: str = field()
    year: str = field()

    @classmethod
    def from_date(cls, title: str, url: str, journal: str, date: str) -> Paper:
        """Strip the date of publication of a paper and return the year.

        Parameters
        ----------
        title : str
            Title of the paper.
        url : str
            Publisher url of the paper.
        journal : str
            Journal of the paper.
        date : str
            Date in which the paper was published.

        Returns
        -------
        Paper
            Container for a paper.
        """
        date_fields = date.split("/")
        if len(date_fields) == 3:
            year, month, day = date_fields
        elif len(date_fields) == 2:
            year, month = date_fields
        else:
            year = date_fields[0]
        return cls(title, url, journal, year)


###############################################################################
# Load functions ##############################################################
###############################################################################

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",  # noqa: B950
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",  # noqa: B950
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",  # noqa: B950
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",  # noqa: B950
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",  # noqa: B950
]


def load_scholar_published_works(config: str) -> list[Paper]:
    """Load Google scholar latest published works.

    Parameters
    ----------
    config : str
        Configuration path for the personal data parameters.

    Returns
    -------
    list[Paper]
        List with dicts containing the title and the journal where the paper was published.
    """
    with open(config) as config_file:
        params = yaml.safe_load(config_file)

    author_id: str = params["scholar"]["author_id"]
    number: int = params["scholar"]["number"]
    timeout: int = params["scholar"]["timeout"]

    base_url = "https://scholar.google.com"

    url = (
        f"{base_url}/citations?hl=en&user={author_id}&view_op=list_works&sortby=pubdate"
    )

    cryptogen = SystemRandom()
    headers = {"User-Agent": cryptogen.choice(USER_AGENTS)}

    response = requests.get(url, headers=headers, timeout=timeout)

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    urls = []
    for paper in soup.find_all("td", {"class": "gsc_a_t"}):
        a_tag = paper.find("a", class_="gsc_a_at")
        if a_tag:
            urls.append(f"{base_url}{a_tag.get('href')}")

    urls = urls[:number]

    papers: list[Paper] = []
    for url in urls:
        cryptogen = SystemRandom()
        headers = {"User-Agent": cryptogen.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        a_tag = soup.find("a", {"class": "gsc_oci_title_link"})
        title = a_tag.text
        link = a_tag["href"]
        for paper_field in soup.find_all("div", {"class": "gs_scl"}):
            field_name = paper_field.find("div", {"class": "gsc_oci_field"}).text
            field_value = paper_field.find("div", {"class": "gsc_oci_value"}).text
            if field_name == "Publication date":
                date = field_value
            elif field_name == "Journal":
                journal = field_value
            else:
                continue
        papers.append(Paper.from_date(title, link, journal, date))

    return papers


def replace_chunk(content: str, marker: str, chunk: str, inline: bool = False) -> str:
    """Replace the content between the marker start and end.

    Parameters
    ----------
    content : str
        The content of the entire file.
    marker : str
        Marker in which the chunk will replace old content.
    chunk : str
        Chunk to replace old content.
    inline : bool, optional
        Keep chunk in the same line, by default False.

    Returns
    -------
    str
        Content with text between marker substituted by chunk.
    """
    r = re.compile(
        rf"<!\-\- {marker} starts \-\->.*<!\-\- {marker} ends \-\->",
        re.DOTALL,
    )
    if not inline:
        chunk = f"\n{chunk}\n"
    chunk = f"<!-- {marker} starts -->{chunk}<!-- {marker} ends -->"
    return r.sub(chunk, content)
