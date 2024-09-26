#!/usr/bin/env python3
"""The module contains data loading functionality."""

###############################################################################
# Imports #####################################################################
###############################################################################

from __future__ import annotations

import re
from dataclasses import dataclass, field
from random import SystemRandom, uniform
from time import sleep

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
    inner_search: bool = params["scholar"]["inner_search"]
    info_pattern: str = params["scholar"]["info_pattern"]
    sleep_time: list[int] = params["scholar"]["sleep_time"]
    sleep_min, sleep_max = sleep_time

    base_url = "https://scholar.google.com"

    url = (
        f"{base_url}/citations?hl=en&user={author_id}&view_op=list_works&sortby=pubdate"
    )

    cryptogen = SystemRandom()
    headers = {"User-Agent": cryptogen.choice(USER_AGENTS)}

    response = requests.get(url, headers=headers, timeout=timeout)

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    out_papers: list[Paper] = []
    for paper in soup.select("#gsc_a_b .gsc_a_t")[:number]:
        title = paper.select_one(".gsc_a_at").text
        url = f"{base_url}{paper.select_one('.gsc_a_at')['href']}"
        info = f"{paper.select_one('.gs_gray+ .gs_gray').text}".replace("\xa0", "")
        match_pattern = re.search(info_pattern, info)

        if match_pattern:
            groups = match_pattern.groupdict()
            year = groups["year"]
            journal = groups["journal"]
        else:
            continue

        out_papers.append(Paper(title, url, journal, year))

    if inner_search:
        papers: list[Paper] = []
        for paper in out_papers:
            cryptogen = SystemRandom()
            headers = {"User-Agent": cryptogen.choice(USER_AGENTS)}
            sleep(uniform(sleep_min, sleep_max))  # nosec
            response = requests.get(paper.url, headers=headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            header = soup.select_one(".gsc_oci_title_link")
            title = header.text
            link = header["href"]
            date, journal = map(
                lambda element: element.text, soup.select(".gsc_oci_value")[1:3]
            )
            papers.append(Paper.from_date(title, link, journal, date))
    else:
        papers = out_papers

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
