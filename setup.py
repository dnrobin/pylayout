from setuptools import setup, find_packages

setup(
    name="pylayout",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "gdspy>=1.5.2",
        "numpy>=1.17",
        "xmltodict>=0.12"
    ],
    author="Daniel Robin",
    author_email="daniel.robin.1@ulaval.ca",
    description="Silicon photonics layout design library",
    keywords="integrated silicon photonics gds gdsii",
    url="https://github.com/robindan/pylayout/"
)