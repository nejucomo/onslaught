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
       the `onslaught` meet the same quality standards.

.. [#] This is strict: any ``warning:`` lines in the `sdist` creation
       command are `onslaught` failures.

.. [#] So your unittests pass. Great! But does your software install?

.. [#] Test the "production" form of your code, not dev source.
