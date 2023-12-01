import logging
from logging.handlers import RotatingFileHandler
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_compress import Compress
from config import Config_is
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()

redis_obj = redis.StrictRedis.from_url(Config_is.REDIS_URL, decode_responses=True)

app = None


def create_app(config_class=Config_is):
    global app
    if app:
        return app
    app = Flask(__name__, template_folder='templates')
    db.init_app(app)
    compress = Compress()
    migrate.init_app(app, db)
    ma = Marshmallow(app)
    CORS(app)
    compress.init_app(app)
    app.config.from_object(config_class)
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1200
    app.config['SQLALCHEMY_POOL_PRE_PING'] = True
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler('log_data.log', maxBytes=10000, backupCount=2)
    file_handler.setFormatter(formatter)
    logging.basicConfig(handlers=[file_handler], level=logging.DEBUG)
    logging.getLogger('log_data.log')
    app.logger.addHandler(file_handler)

    @app.teardown_request
    def teardown_request(exception=None):
        if db is not None:
            db.session.close()
            db.engine.dispose()

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/v1')

    return app


from app import models
