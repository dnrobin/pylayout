#!/usr/local/bin/python3

from setuptools import setup, find_packages

raise SystemError("Unreleased version cannot install!")

import pylayout

setup(
    name="pylayout",
    version=pylayout.__version__,
    description="A silicon photonicsm layout design library",
    long_description=README + "\n\n" + CHANGELOG,
    long_description_type="text/markdown",
    license="MIT",
    author="Daniel Robin",
    author_email="daniel.robin.1@ulaval.ca",
    keywords=["integrated", "silicon", "photonics", "gds", "gdsii", "nano", "lithography"],
    url="https://github.com/robindan/pylayout/",
    download_url='https://pypi.org/project/pylayout/',
    packages=find_packages()
)

install_requires=[
    "gdspy>=1.5",
    "numpy>=1.17",
    "xmltodict>=0.12"
]

if __name__ == '__main__':
    setup(**setup_args, 
        install_requires=install_requires,
        include_package_data=True)
