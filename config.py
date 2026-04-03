import os
from dotenv import load_dotenv
load_dotenv()  # Add this at the top of your config.py
class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    # Prefer DATABASE_URL; fallback only for local quick start/dev if not set.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True

class ProductionConfig(Config):
    """Production config."""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing config."""
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig





    
}
