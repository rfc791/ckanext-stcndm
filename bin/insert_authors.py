#!/usr/bin/env python
# encoding: utf-8
import sys
import csv
from collections import namedtuple

import ckanapi
from docopt import docopt


USAGE = """insert_authors.py

Usage:
    insert_authors.py <remote> <package_id> <source> [options]

Options:
    --api-key=<key>         API Key to use for insertion.
"""

record = namedtuple('record', ['full_name', 'first_name', 'last_name'])


def main():
    args = docopt(USAGE)

    rc = ckanapi.RemoteCKAN(
        args['<remote>'],
        apikey=args['--api-key']
    )

    with open(args['<source>'], 'rU') as fin:
        reader = csv.DictReader(fin)

        results = set(
            record(
                '{0}, {1}'.format(
                    r['last_name'].title(),
                    r['first_name'].title()
                ),
                r['first_name'].title(),
                r['last_name'].title()
            ) for r in reader
        )

        rc.action.datastore_create(
            resource={
                'package_id': args['<package_id>']
            },
            fields=[{
                'id': 'first_name',
                'type': 'text'
            }, {
                'id': 'last_name',
                'type': 'text'
            }, {
                'id': 'full_name',
                'type': 'text'
            }],
            aliases=[
                'internal_authors'
            ],
            primary_key=[
                'first_name',
                'last_name'
            ],
            records=list(r._asdict() for r in results)
        )


if __name__ == '__main__':
    sys.exit(main())
