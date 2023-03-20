#!/usr/bin/env python

import os
from setuptools import setup
from setuptools import find_packages
from pathlib import Path


def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding="utf-8") as file:
        return file.read()


def version():
    """Get the local package version."""
    namespace = {}
    path = Path("civicrmapi", "__version__.py")
    exec(path.read_text(), namespace)
    return namespace["__version__"]


version = version()
if 'dev' in version:
    dev_status = 'Development Status :: 3 - Alpha'
elif 'beta' in version:
    dev_status = 'Development Status :: 4 - Beta'
else:
    dev_status = 'Development Status :: 5 - Production/Stable'


setup(
    name="civicrmapi",
    version=version,
    description="Connect with the CiviCRM APIv4.",
    long_description=read("README.rst"),
    author="Thomas Leichtfuß",
    author_email="thomas.leichtfuss@posteo.de",
    license="BSD License",
    url="https://github.com/thomst/civicrmapi",
    platforms=["OS Independent"],
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "requests",
        "invoke",
    ],
    classifiers=[
        dev_status,
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
    ],
    zip_safe=True,
)
