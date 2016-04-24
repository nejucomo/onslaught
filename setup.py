#! /usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='onslaught',
    version='0.1.dev2',
    author='Nathan Wilcox',
    author_email='nejucomo@gmail.com',
    license='GPLv3',
    url='https://github.com/nejucomo/onslaught',

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'onslaught = onslaught.main:main',
            'onslaught-check-sdist-log = onslaught.check_sdist_log:main',
            ],
        },

    install_requires=[
        'flake8 >= 2.0',
        'coverage >= 3.6',
        'virtualenv >= 13.1.2',
        ],
    )
