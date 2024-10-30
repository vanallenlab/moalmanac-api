from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

    with app.app_context():
        from . import routes

    return app
