"""Resume."""

# read version from installed package
from importlib.metadata import version
__version__ = version("resume")

# populate package namespace
from resume.resume import *