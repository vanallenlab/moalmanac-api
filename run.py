import argparse

from app import create_app

app = create_app()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        prog='Molecular Oncology Almanac API',
        description='REST API for the Molecular Oncology Almanac database'
    )
    arg_parser.add_argument(
        '-d', '--development',
        help='Run the API in development',
        action='store_true'
    )
    args = arg_parser.parse_args()

    if args.development:
        host = 'localhost'
        port = 8000
        debug = True
    else:
        host = '0.0.0.0'
        port = 5000
        debug = False

    app.run(host=host, port=port, debug=debug)
