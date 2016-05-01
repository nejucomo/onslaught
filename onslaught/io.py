"""Wrap all I/O to allow test specifications at this layer."""

import os
import errno
import shutil
import subprocess
import logging


CalledProcessError = subprocess.CalledProcessError
STDOUT = subprocess.STDOUT


class IOProvider (object):
    def __init__(self):
        self._debug = logging.getLogger('IOProvider').debug

        self.environ = os.environ

        delegatees = [
            os.chdir,
            os.getcwd,
            os.listdir,
            os.path.abspath,
            os.path.basename,
            os.path.dirname,
            os.path.exists,
            os.path.expanduser,
            os.path.isabs,
            os.path.isfile,
            os.path.join,
            os.walk,
            subprocess.check_call,
            ]

        for d in delegatees:
            setattr(self, d.__name__, d)

    # Subprocess I/O:
    def gather_output(self, *args):
        return subprocess.check_output(args).strip()

    def run(self, args, **kw):
        return subprocess.check_call(args, **kw)

    # File I/O:
    def copyfile(self, src, dst):
        self._debug('cp %r %r', src, dst)
        shutil.copyfile(src, dst)

    def copytree(self, src, dst):
        self._debug('cp -r %r %r', src, dst)
        shutil.copytree(src, dst, symlinks=True)

    def ensure_is_directory(self, path):
        try:
            os.makedirs(path)
        except os.error as e:
            if e.errno != errno.EEXIST:
                raise
            else:
                # It already existed, no problem:
                return
        else:
            self._debug('Created %r', path)

    def open(self, path, mode):
        return file(path, mode)

    def read(self, path):
        with self.open(path, 'r') as f:
            return f.read()

    def write(self, path, contents):
        with self.open(path, 'w') as f:
            return f.write(contents)

    def rmtree(self, path):
        self._debug('rm -rf %r', path)
        try:
            shutil.rmtree(path)
        except os.error as e:
            if e.errno != errno.ENOENT:
                raise


provider = IOProvider()
