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
import os
from flask_jwt_extended import JWTManager
from flask_session import Session

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
sess = Session()
compress = Compress()

# Initialize Redis only if REDIS_URL is set
redis_obj = None
if Config_is.REDIS_URL:
    redis_obj = redis.StrictRedis.from_url(Config_is.REDIS_URL, decode_responses=True)

app = None


def create_app(config_name='dev'):
    """Create Flask application."""
    global app
    if app:
        return app
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config_is)
    
    # Ensure database URI is set
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'app.db')
    
    # Ensure session configuration is set
    if not app.config.get('SESSION_TYPE'):
        app.config['SESSION_TYPE'] = 'filesystem'
    
    db.init_app(app)
    migrate.init_app(app, db)
    ma = Marshmallow(app)
    CORS(app, supports_credentials=True)
    compress.init_app(app)
    jwt.init_app(app)
    sess.init_app(app)
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1200
    app.config['SQLALCHEMY_POOL_PRE_PING'] = True
    app.config['SESSION_REDIS'] = redis.from_url(app.config['REDIS_URL'])
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
    from app.api.auth import auth_bp
    from app.api.store import store_bp
    from app.api.product import product_bp
    
    app.register_blueprint(api_bp, url_prefix='/v1')
    app.register_blueprint(auth_bp, url_prefix='/v1/auth')
    app.register_blueprint(store_bp, url_prefix='/v1/store')
    app.register_blueprint(product_bp, url_prefix='/v1/product')

    return app


from app import models
