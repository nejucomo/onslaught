import os
import errno
import shutil
import logging


class Path (object):
    def __init__(self, path):
        self._p = os.path.abspath(path)
        self._log = logging.getLogger('path')

    @property
    def basename(self):
        return os.path.basename(self._p)

    @property
    def exists(self):
        return os.path.exists(self._p)

    @property
    def parent(self):
        return Path(os.path.dirname(self._p))

    def __hash__(self):
        return hash(self._p)

    def __eq__(self, other):
        return isinstance(other, Path) and other._p == self._p

    def __repr__(self):
        return repr(self._p)

    def __str__(self):
        return self._p

    def __call__(self, *parts):
        return Path(os.path.join(self._p, *parts))

    def __iter__(self):
        for n in os.listdir(self._p):
            yield self(n)

    def cleanup_session(self):
        return _CleanupSession(self)

    def ensure_is_directory(self):
        try:
            os.makedirs(self._p)
        except os.error as e:
            if e.errno != errno.EEXIST:
                raise
            else:
                # It already existed, no problem:
                return
        else:
            self._log.debug('Created %r', self)

    def listdir(self):
        return list(self)

    def open(self, mode):
        return file(self._p, mode)

    def pushd(self):
        return _PushdContext(self)

    def rmtree(self):
        self._log.debug('rm -rf %r', self)
        try:
            shutil.rmtree(self._p)
        except os.error as e:
            if e.errno != errno.ENOENT:
                raise

    def walk(self):
        for bd, ds, fs in os.walk(self._p):
            bd = Path(bd)
            for n in ds + fs:
                yield bd(n)


Home = Path(os.environ['HOME'])


class _PushdContext (object):
    def __init__(self, dest):
        self._d = dest
        self._old = os.getcwd()

    def __enter__(self):
        os.chdir(str(self._d))
        return self._d

    def __exit__(self, *a):
        os.chdir(self._old)


class _CleanupSession (object):
    def __init__(self, target):
        self._target = target

    def __enter__(self):
        self._manifest = set(self._target.walk())
        return self._target

    def __exit__(self, *a):
        log = logging.getLogger('cleanup').debug
        log(
            'Cleaning up anything created in %r during session',
            self._target,
        )

        for p in self._target.walk():
            if p not in self._manifest and p.exists:
                p.rmtree()
