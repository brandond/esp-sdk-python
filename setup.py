#!/usr/bin/env python
from setuptools import setup, find_packages
import sys
import re
if sys.version_info[0] == 2:
    from io import open

with open('./README.rst', mode='r', encoding='utf-8') as f:
    readme = f.read()

with open('esp/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

setup(
    name='esp',
    version=version,
    description='Evident Security Platform (ESP) SDK for Python',
    long_description=readme,
    author='Kyle Terry',
    author_email='kyle@evident.io',
    packages=find_packages(),
    package_data={'esp': ['packages/requests/*.pem']},
    py_modules=['esp'],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
    ),
    install_requires=[
        'requests',
        'six',
    ],
    tests_require=[
        'coverage',
        'mock',
        'nose',
        'unittest2',
    ],
)
