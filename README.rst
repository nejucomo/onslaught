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

`onslaught`:

- does not require your package's users to install it,
- has minimal configuration and customization [#]_,
- leaves your source directory the way it found it,
- leaves your base python packages unmodified,
- ensures your project generates a clean `sdist` [#]_,
- tests the `sdist` install process [#]_,
- runs unittests against the installed package [#]_,
- and generates branch coverage reports.

.. [#] No tests can be customized or disabled. All packages which pass
       the `onslaught` meet the same quality standards. The users current
       directory has no effect. Where possible, other configurability
       will be removed.

.. [#] This is strict: any ``warning:`` lines in the `sdist` creation
       command are `onslaught` failures.

.. [#] So your unittests pass. Great! But does your software install?

.. [#] Test the "production" form of your code, not dev source.

Quick Start
===========

Installation
------------

First, install with pip:

.. code:: bash

   $ pip install onslaught

Running
-------

Now run it against your projects:

.. code:: bash

   $ onslaught /path/to/my/project

-or:

.. code:: bash

   $ cd /path/to/my/project ; onslaught

This runs a series of "test phases" and then generates coverage
reports. The output is concise; details for a test phase are only
displayed if that phase fails.

(Onslaught never modifies the project directory, nor the current
directory.)

Diagnosis
---------

Each run of onslaught on a project will create a fresh directory at
``~/.onslaught/results/${PROJECT_NAME}``. If this directory exists when
starting a new onslaught run, it is removed, so that the contents of this
directory are always self-consistent and are specific to the last
run.

This results directory has a few important subdirectories:

``logs/``
  This contains a ``main.log`` that describes high level operation,
  including all subcommand arguments, so you can rerun any of these
  commands manually. It also contains a log for each subcommand run
  separately, prefixed with a decimal ordering, so you can always see
  the complete output of each command.

``coverage/``
  The HTML generated coverage report. Open ``index.html`` with your
  browser. Notice you can sort the table by clicking column headers or
  using the keybindings (help found by clicking keyboard icon).

``dist/``
  This contains the result of ``./setup.py sdist``, so you can
  interactively test the same source distribution that is used for
  installation and unit testing by onslaught.

``venv/``
  This is the `virtualenv` used to test the package installation. You
  could interactively experiment with your project here.


Status
======

This is "alpha" code. There are no unittests, so this project doesn't (yet) follow it's own prescription (see `#8`_). :-(

.. _`#8`: https://github.com/nejucomo/onslaught/issues/8

Roadmap
=======

Once it has thorough test coverage and a handful of users have notified
me that they've used it successfully, or filed bugs, then I will release
'0.1' after fixing a subset of the bugs.

The goal for 1.0 is to have the "right" inflexible criteria (see
`Philosophy`_) baked into `onslaught`. For example, maybe it should
generate and test ``wheel`` instead of ``sdist``, or maybe it should
test both. It should work with python 2 and 3.

At that point, my vision is for `onslaught` to be automatically run
against all python packages (eg on PyPI) and the results published
somewhere.

Philosophy
==========

`onslaught` is a "badge". Tested software conforms to the `onslaught`,
not vice versa. Therefore, a large fraction of software will not pass
`onslaught` tests, especially popular and/or slowly evolving
packages. This is fine.

There should be no reason you don't run it against your codebase. If it
fails and your codebase has legacy concerns, c'est la vie. If, on the
other hand, you want to achieve and preserve the `onslaught` badge of
awesomeness, then go for it. ;-)

**Note:** Currently `onslaught` is a prototype in flux, so take the
above with a grain of salt.

Related Work
============

The `tox`_ project has similar goals, specifically automating the testing of packaging itself on different python versions. It doesn't aim to define a "badge of quality" and is more flexible.

.. _`tox`: https://testrun.org/tox/latest/
