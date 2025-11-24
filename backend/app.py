import os
import sys
from flask import Flask, render_template
from werkzeug.debug import DebuggedApplication
import logging

from backend.database.models import *
from backend.database.models import db


# Flask quickstart:
# https://flask.palletsprojects.com/en/3.0.x/quickstart/
# Flask factory pattern:
# https://flask.palletsprojects.com/en/3.0.x/tutorial/factory/

def create_app():
    
    STATIC_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))


    # Create and configure the backend
    app = Flask(__name__,
                instance_relative_config=False,
                static_folder=STATIC_FOLDER,
                static_url_path='/static'
    )


    # Load config from file config.py
    app.config.from_pyfile('config.py')
    
    #setting log level
    app.logger.setLevel(logging.INFO)

    # Keep static files path in backend config
    app.config["STATIC_FOLDER"] = STATIC_FOLDER


    # Enable debug mode - you will see beautiful error messages later :)
    # https://flask.palletsprojects.com/en/3.0.x/debugging/
    app.debug = True
    app.wsgi_app = DebuggedApplication(app.wsgi_app)


    # Ensure the instance folder exists - nothing interesting now
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    

    # https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/#configure-the-extension
    # Allow database path override via FLASK_DB_PATH env or --db-path argument
    db_path = os.environ.get("FLASK_DB_PATH")
    if not db_path:
        # Check for --db-path in sys.argv
        for idx, arg in enumerate(sys.argv):
            if arg == "--db-path" and idx + 1 < len(sys.argv):
                db_path = sys.argv[idx + 1]
                break
    if not db_path:
        db_path = f"{os.getcwd()}/instance/database.sqlite"

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Setup custom "Not found" page
    # https://flask.palletsprojects.com/en/3.0.x/errorhandling/#custom-error-pages
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Defining components
    from .components.qrcode.qrcodeController import bp as bp_download
    app.register_blueprint(bp_download)
    
    return app


