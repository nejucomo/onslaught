#! /usr/bin/env python

import sys
import subprocess
import setuptools


PACKAGE = 'onslaught'
VERSION = '0.1.dev2'
CODE_SIGNING_GPG_ID = '29F306D804101C610BDEA41F5F53C65730693904'


def setup():
    setuptools.setup(
        name=PACKAGE,
        version=VERSION,
        author='Nathan Wilcox',
        author_email='nejucomo@gmail.com',
        license='GPLv3',
        url='https://github.com/nejucomo/{}'.format(PACKAGE),

        packages=setuptools.find_packages(),

        entry_points={
            'console_scripts': [
                '{0} = {0}.main:main'.format(PACKAGE),
                ('{0}-check-sdist-log = {0}.check_sdist_log:main'
                 .format(PACKAGE)),
            ],
        },

        install_requires=[
            'flake8 >= 2.0',
            'coverage >= 3.6',
            'virtualenv >= 13.1.2',
        ],
    )


def main(args=sys.argv[1:]):
    if args == ['release']:
        publish_release()
    else:
        setup()


def publish_release():
    # TODO: require self-onslaught to pass as policy.
    # ref: https://github.com/nejucomo/onslaught/issues/8

    def sh(*args):
        print 'Running {!r}...'.format(args)
        return subprocess.check_call(args)

    def shout(*args):
        print 'Running {!r}...'.format(args)
        return subprocess.check_output(args)

    gitstatus = shout('git', 'status', '--porcelain')
    if gitstatus.strip():
        raise SystemExit(
            'ABORT: dirty working directory:\n{}'.format(
                gitstatus,
            )
        )

    branch = shout('git', 'rev-parse', '--abbrev-ref', 'HEAD').strip()
    if branch != 'release':
        raise SystemExit(
            'ABORT: must be on release branch, not {!r}'.format(
                branch,
            ),
        )

    version = shout('python', './setup.py', '--version').strip()
    print 'Creating git tag: {!r}'.format(version)
    sh('git', 'tag', version)

    print 'Uploading sdist...'
    sh(
        'python',
        './setup.py',
        'sdist',
        'upload',
        '--sign',
        '--identity', CODE_SIGNING_GPG_ID,
    )


if __name__ == '__main__':
    main()
