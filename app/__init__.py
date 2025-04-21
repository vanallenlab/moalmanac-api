import flask
from . import database
from . import models
from .blueprints import main


def create_app(config_path='config.ini'):
    app = flask.Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.json.sort_keys = False

    engine, session = database.init_db(config_path=config_path)
    models.Base.metadata.create_all(bind=engine)

    app.register_blueprint(main.main_bp)
    app.config['SESSION'] = session

    return app
