import dotenv
import os

from app import create_app

dotenv.load_dotenv(override=False)
app = create_app()


if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = bool(os.environ.get('FLASK_DEBUG', False))

    app.run(host=host, port=port, debug=debug)
