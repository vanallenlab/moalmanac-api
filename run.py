import argparse

from app import create_app

app = create_app()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        prog='Molecular Oncology Almanac API',
        description='REST API for the Molecular Oncology Almanac database'
    )
    arg_parser.add_argument(
        '-m', '--mode',
        choices=['development', 'production'],
        default='development',
        help='Run the API in development or production mode'
    )
    args = arg_parser.parse_args()

    if args.mode == 'development':
        host = 'localhost'
        port = 8000
        debug = True
    elif args.mode == 'production':
        host = '0.0.0.0'
        port = 5000
        debug = False
    else:
        raise ValueError(f'Invalid mode: {args.mode}')

    app.run(host=host, port=port, debug=debug)

