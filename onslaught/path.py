from onslaught import io


class Path (object):
    @classmethod
    def from_relative(cls, relpath):
        return cls(io.provider.abspath(relpath))

    def __init__(self, path):
        assert io.provider.isabs(path)
        self._p = path

    @property
    def pathstr(self):
        return self._p

    @property
    def basename(self):
        return io.provider.basename(self._p)

    @property
    def exists(self):
        return io.provider.exists(self._p)

    @property
    def parent(self):
        return Path(io.provider.dirname(self._p))

    @property
    def isfile(self):
        return io.provider.isfile(self._p)

    def __hash__(self):
        return hash(self._p)

    def __eq__(self, other):
        return isinstance(other, Path) and other._p == self._p

    def __repr__(self):
        return 'Path({!r})'.format(self._p)

    def __call__(self, *parts):
        return Path(io.provider.join(self._p, *parts))

    def __iter__(self):
        for n in io.provider.listdir(self._p):
            yield self(n)

    def copyfile(self, dst):
        return io.provider.copyfile(self._p, dst.pathstr)

    def copytree(self, dst):
        return io.provider.copytree(self._p, dst.pathstr)

    def ensure_is_directory(self):
        io.provider.ensure_is_directory(self._p)

    def listdir(self):
        return list(self)

    def open(self, mode):
        return io.provider.open(self._p, mode)

    def read(self):
        return io.provider.read(self._p)

    def write(self, contents):
        return io.provider.write(self._p, contents)

    def pushd(self):
        return _PushdContext(self)

    def rmtree(self):
        io.provider.rmtree(self._p)

    def walk_files(self):
        for (bd, ds, fs) in io.provider.walk(self._p):
            bd = Path(bd)
            for f in fs:
                yield bd(f)


Home = Path(io.provider.abspath(io.provider.environ['HOME']))


class _PushdContext (object):
    def __init__(self, dest):
        self._d = dest
        self._old = io.provider.getcwd()

    def __enter__(self):
        io.provider.chdir(self._d.pathstr)
        return self._d

    def __exit__(self, *a):
        io.provider.chdir(self._old)
