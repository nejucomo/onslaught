#! /usr/bin/env python

import os
import subprocess
import setuptools
import distutils.command.upload


PACKAGE = 'onslaught'
VERSION = '0.1.dev3'
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
            'virtualenv >= 13.1.2',

            # For self-unittests, not target testing:
            'mock >= 2.0.0',
        ],

        test_suite='{}.tests'.format(PACKAGE),

        cmdclass={
            'release': ReleaseCommand,
            'upload': UploadCommand,
        },
    )


class ReleaseCommand (setuptools.Command):
    """Prepare and distribute a release"""

    description = __doc__

    user_options = [
        ('dry-run', None, 'Do not git tag or upload.')
    ]

    _SAFETY_ENV = '_ONSLAUGHT_SETUP_RELEASE_ALLOW_UPLOAD_'

    def initialize_options(self):
        """init options"""
        self.dry_run = False

    def finalize_options(self):
        """finalize options"""
        pass

    def run(self):
        # TODO: require self-onslaught to pass as policy.
        # ref: https://github.com/nejucomo/onslaught/issues/8

        def fmt_args(args):
            return ' '.join([repr(a) for a in args])

        def make_sh_func(subprocfunc):
            def shfunc(*args):
                print 'Running: {}'.format(fmt_args(args))
                try:
                    return subprocfunc(args)
                except subprocess.CalledProcessError as e:
                    raise SystemExit(str(e))
            return shfunc

        def dry_run(*args):
            print 'Not running (--dry-run): {}'.format(fmt_args(args))

        sh = make_sh_func(subprocess.check_call)
        shout = make_sh_func(subprocess.check_output)
        shdry = dry_run if self.dry_run else sh

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
        shdry('git', 'tag', version)

        os.environ[ReleaseCommand._SAFETY_ENV] = 'yes'

        shdry(
            'python',
            './setup.py',
            'sdist',
            'upload',
            '--sign',
            '--identity', CODE_SIGNING_GPG_ID,
        )


class UploadCommand (distutils.command.upload.upload):
    description = distutils.command.upload.upload.__doc__

    def run(self):
        if os.environ.get(ReleaseCommand._SAFETY_ENV) != 'yes':
            raise SystemExit(
                'Please use the release command, ' +
                'rather than directly uploading.')
        else:
            return distutils.command.upload.upload.run(self)


if __name__ == '__main__':
    setup()
