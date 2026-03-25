import argparse
import os
from app import app
import auth
import api
import admin
from config import config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', default='development', choices=['development', 'production', 'testing'])
    args = parser.parse_args()

    app.config.from_object(config[args.env])

    # Development mode: force local sqlite (avoids remote DB timeouts while developer is on laptop)
    if args.env == 'development':
        app.logger.warning('development env: forcing local sqlite database URI')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'

    # Initialize DB after config is set (prevents outdated DB URI from first import)
    from app import init_app_database
    init_app_database()

    app.run(host='0.0.0.0', port=5000, debug=True)
