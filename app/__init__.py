import flask
from . import database
from . import models


def create_app(config_path='config.ini'):
    app = flask.Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.json.sort_keys = False

    engine, session_factory = database.init_db(config_path=config_path)
    models.Base.metadata.create_all(bind=engine)

    app.config['SESSION_FACTORY'] = session_factory

    from .blueprints import main
    app.register_blueprint(main.main_bp)

    return app
