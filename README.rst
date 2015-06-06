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

.. code:: bash

   $ git clone 'https://github.com/nejucomo/onslaught'
   $ cd onslaught
   $ pip install .
   $ onslaught .

Roadmap
=======

Once it has thorough test coverage and a handful of users have notified
me that they've used it successfully, or filed bugs, then I will release
'0.1' after fixing a subset of the bugs.

Philosophy
==========

`onslaught` is a "badge". Tested software conforms to the `onslaught`,
not vice versa. Therefore, a large fraction of software will not pass
`onslaught` tests, especially popular and/or slowly evolving
packages. This is fine.

`onslaught`:

- does not require your package's users to install it,
- has minimal configuration and customization [#]_,
- leaves your source directory the way it found it,
- leaves your base python packages unmodified,
- ensures your project generates a clean `sdist` [#]_,
- tests the `sdist` install process [#]_,
- runs unittests against the installed process [#]_,
- and always generates branch coverage reports.

In other words, there should be no reason you don't run it against
your codebase. If it fails and your codebase has legacy concerns, c'est
la vie. If, on the other hand, you want to achieve and preserve the
`onslaught` badge of awesomeness, then go for it. ;-)

.. [#] No tests can be customized or disabled. All packages which pass
       the `onslaught` meet the same quality standards. The users current
       directory has no effect. Where possible, other configurability
       will be removed.

.. [#] This is strict: any ``warning:`` lines in the `sdist` creation
       command are `onslaught` failures.

.. [#] So your unittests pass. Great! But does your software install?

.. [#] Test the "production" form of your code, not dev source.

**Note:** Currently `onslaught` is a prototype in flux, so take the
above with a grain of salt.
