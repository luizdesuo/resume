"""Nox sessions."""
from pathlib import Path
import nox


_package = "resume"
_python_versions = ["3.11"]

nox.options.sessions = (
    "safety",
    "typeguard",
    "tests",
    "docs",
)


@nox.session(python=_python_versions)
def safety(session: nox.Session) -> None:
    """Scan dependencies for insecure packages."""
    session.install(".[test]")
    session.run("safety", "check", "--full-report")

@nox.session(python=_python_versions)
def typeguard(session: nox.Session) -> None:
    """Runtime type checking using Typeguard."""
    session.install(".[test]")
    session.run("pytest", f"--typeguard-_packages={_package}", *session.posargs)

@nox.session(python=_python_versions)
def tests(session: nox.Session) -> None:
    """Run the test and xdoctest suites."""
    session.install(".[test]")
    session.run("pytest",
                "--cov=resume",
                "--cov-report=xml",
                "--xdoctest",
                *session.posargs)

@nox.session
def docs(session: nox.Session) -> None:
    with open(Path("docs/requirements.txt")) as f:
        requirements = f.read().splitlines()
    session.install(".[docs]")
    session.install(*requirements)
    session.chdir("docs")
    session.run("rm", "-rf", "_build/", external=True)
    build_dir = Path("docs", "_build", "html")

    if "serve" in session.posargs:
        sphinx_args = ["-W", ".", "--watch", ".", "--open-browser", str(build_dir)]
        session.run("sphinx-autobuild", *sphinx_args)
    else:
        sphinx_args = ["-W", ".", str(build_dir)]
        session.run("sphinx-build", *sphinx_args)