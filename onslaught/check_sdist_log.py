import sys
import re
import argparse


Description = """\
Perform a strict check on the output of `setup.py sdist`: if it contains
any warnings, print them and exit with an error.
"""

FailureRgx = re.compile(r'^warning:.*$')


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=Description)
    arghelp = 'A file containing the output of `setup.py sdist`.'
    parser.add_argument('SETUP_SDIST_LOG', help=arghelp)
    opts = parser.parse_args(args)

    exitstatus = 0
    with file(opts.SETUP_SDIST_LOG, 'r') as f:
        for line in f:
            if FailureRgx.match(line):
                sys.stdout.write(line)
                exitstatus = 1

    raise SystemExit(exitstatus)
