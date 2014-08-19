#! /usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='onslaught',
    version='0.1.dev0',
    author='Nathan Wilcox',
    author_email='nejucomo@gmail.com',
    license='GPLv3',

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'onslaught = onslaught.main:main',
            ],
        },

    install_requires=[
        'flake8 >= 2.0',
        'coverage >= 3.6',
        ],
    )
