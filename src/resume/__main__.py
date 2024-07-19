#!/usr/bin/env python3
"""Command-line interface."""

###############################################################################
# Imports #####################################################################
###############################################################################

import typing
from pathlib import Path

import click
import yaml  # type: ignore

import resume


###############################################################################
# CLI group ###################################################################
###############################################################################


@typing.no_type_check
@click.group()
@click.version_option()
def main() -> None:
    """Resume."""


###############################################################################
# Load functions ##############################################################
###############################################################################


@typing.no_type_check
@main.command()
@click.option(
    "--config",
    default=Path("params.yaml"),
    help=f"""Configuration path for the data loader parameters,
    default path is {Path('params.yaml')}.""",
)
def update_latest_works(config: str) -> None:
    """Update latest published works.

    This function combines `load_scholar_published_works` and
    `replace_chunk` into a single CLI command to change
    `README.md` file.

    Parameters
    ----------
    config : str
        Configuration path for the data loader parameters.
    """
    with open(config) as config_file:
        params = yaml.safe_load(config_file)

    marker = params["scholar"]["marker"]

    click.echo("Loading personal data from scholar.")

    latest_works = resume.load_scholar_published_works(config)

    click.echo("Personal data retrieved from scholar")

    click.echo("Updating latest works.")

    entries_md = "\n".join(
        ["* {title} (_{journal}_)".format(**entry) for entry in latest_works]
    )

    readme_path = Path("README.md")
    readme = readme_path.open().read()

    rewritten_entries = resume.replace_chunk(readme, marker, entries_md)
    readme_path.open("w").write(rewritten_entries)

    click.echo("Latest works updated.")


###############################################################################
# CLI run #####################################################################
###############################################################################


if __name__ == "__main__":
    main(prog_name="resume")  # pragma: no cover
