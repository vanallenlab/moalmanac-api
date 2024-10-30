import argparse
from app import database

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        prog='Wrapper to create MOAlmanac SQLite3 file from referenced JSONs',
        description='Using referenced JSON files, create SQLite3 db'
    )
    arg_parser.add_argument(
        '--input',
        '-i',
        default='data/referenced',
        help='Directory for referenced moalmanac db json files'
    )
    args = arg_parser.parse_args()
    database.main(
        referenced_dictionary=args.input
    )
