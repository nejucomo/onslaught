import sys
import argparse
import logging


DESCRIPTION = """\
Run the target python project through a battery of tests.
"""


def main(args = sys.argv[1:]):
    opts = parse_args(args)
    logging.debug('Parsed opts: %r', opts)
    raise NotImplementedError(repr(main))


def parse_args(args):
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    loggroup = parser.add_mutually_exclusive_group()

    loggroup.add_argument(
        '--quiet',
        action='store_const',
        const=logging.WARN,
        dest='loglevel',
        help='Only log warnings and errors.')

    loggroup.add_argument(
        '--debug',
        action='store_const',
        const=logging.DEBUG,
        dest='loglevel',
        help='Log everything.')

    parser.add_argument(
        'TARGET',
        type=str,
        default='.',
        help='Target python source.')

    opts = parser.parse_args(args)

    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname) 5s %(name)s | %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z',
        level=opts.loglevel)

    return opts
