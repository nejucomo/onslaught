#! /usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='onslaught',
    version='0.1.dev0',
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
        # All of these dependencies are used for subprocesses, not
        # modules, so hopefully this puts these utilities on PATH:
        'coverage == 3.7.1',
        'flake8 == 2.4',
        'twisted == 15.2',
        ],
    )
