=========
onslaught
=========

Run style and static checks against a python codebase, execute automated
tests with coverage.

Specific tests are:

* PEP8 style.
* pyflakes static checks.
* sdist creation and installation.
* unittests.

It also generates branch-coverage reports.

Status
======

This is "alpha" code. There are no unittests, which you can see by
running the development commit acceptance process I've been using:

```bash
$ git clone 'https://github.com/nejucomo/onslaught'
$ cd onslaught
$ pip install .
$ onslaught .
```

Roadmap
=======

Once it has thorough test coverage and a handful of users have notified
me that they've used it successfully, or filed bugs, then I will release
'0.1' after fixing a subset of the bugs.

Philosophy
==========

`onslaught`:

- does not require your package's users to install it,
- has minimal configuration and customization [#]_,
- leaves your source directory the way it found it,
- leaves your base python packages unmodified,
- ensures your project generates a clean `sdist` [#]_,
- tests the `sdist` install process [#]_,
- runs unittests against the installed process [#]_,
- and always generates branch coverage reports.

.. [#] No tests can be customized or disabled. All packages which pass
       the `onslaught` meet the same quality standards. The users current
       directory has no effect. Where possible, other configurability
       will be removed.

.. [#] This is strict: any ``warning:`` lines in the `sdist` creation
       command are `onslaught` failures.

.. [#] So your unittests pass. Great! But does your software install?

.. [#] Test the "production" form of your code, not dev source.
