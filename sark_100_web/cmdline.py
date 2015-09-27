import argparse
import logging
import six
import sys

from .web import app


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'serial_port',
        help='Serial port to which your antenna analyzer is connected',
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        type=six.text_type
    )
    parser.add_argument(
        '--port',
        default=8000,
        type=int
    )
    args = parser.parse_args(args)

    logging.basicConfig(level=logging.INFO)

    app.config['SERIAL_PORT'] = args.serial_port
    app.run(
        host=args.host,
        port=args.port,
    )
