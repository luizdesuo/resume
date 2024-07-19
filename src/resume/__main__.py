"""Command-line interface."""
import click


@click.group()
@click.version_option()
def main() -> None:
    """Resume."""

@main.command()
def hello() -> None:
    click.echo(f"Hello")


if __name__ == "__main__":
    main(prog_name="resume")  # pragma: no cover
