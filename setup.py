# -*- coding: utf-8 -*-

import setuptools
import distutils.text_file
from pathlib import Path
from typing import List


with open("README.md", "r") as fh:
    long_description = fh.read()


def _parse_requirements(filename: str) -> List[str]:
    """Return requirements from requirements file."""
    # Ref: https://stackoverflow.com/a/42033122/
    return distutils.text_file.TextFile(filename=str(Path(__file__).with_name(filename))).readlines()


setuptools.setup(
    name="chaikin3d",
    version="0.1.0",
    author="Giussepi Lopez",
    author_email="giussepexy@gmail.com",
    description="Expansion of the Chaikin Algorithm to 3D space (polyhedra)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/giussepi/Chaikin3D",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=_parse_requirements('requirements.txt'),
)
