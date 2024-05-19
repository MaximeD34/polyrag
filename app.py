#for the env variables
import os
#--

#for flask
from flask import Flask, request
from flask import jsonify
#--

#for the database
from flask_sqlalchemy import SQLAlchemy
from database import db
from models import Users
#--

#for the routes
from user_routes import user_routes
from login_routes import login_routes
from files_routes import files_routes
from ai_routes import ai_routes
#--

#global variable for the storage path
storage_path = os.getenv('STORAGE_PATH', '/home/maxime/PolyRag/backend/../local_test_persistent_storage/')
#

def create_app():

    print("app was created")
    #local db url : postgres://postgres:{password}@localhost:5432/polyrag_db
    #dokku db url : postgres://postgres:46a6bd3aecb7e1e47348ccd270ba10e4@dokku-postgres-polyrag-db:5432/polyrag_db

    app = Flask(__name__)
    
    #configure the database
    local_password = os.getenv('POLYRAG_DB_PASSWORD')
    
    url = os.getenv('DATABASE_URL', f'postgres://postgres:{local_password}@localhost:5432/polyrag_db')
    #change the first postgres to postgresql for the url
    url = url.replace('postgres', 'postgresql', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = url
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    #-- end of database configuration

    #register the routes
    app.register_blueprint(user_routes)
    app.register_blueprint(login_routes)
    app.register_blueprint(files_routes)
    app.register_blueprint(ai_routes)
    #--

    from embeddings_manager import create_all_unexisting_embedding

    # with app.app_context():
    #     create_all_unexisting_embedding(storage_path)

    return app

from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
from datetime import timedelta
def create_jwt():
    #initialize the jwt
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'local_jwt_secret_key')
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    app.config['JWT_CSRF_CHECK_FORM'] = False
    app.config['JWT_CSRF_METHODS'] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=14)
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    app.config['JWT_COOKIE_SECURE'] = False  # TODO Set to True if using HTTPS
    if os.getenv('FLASK_ENV') == 'production':
        app.config['JWT_COOKIE_DOMAIN'] = '.cluster-ig3.igpolytech.fr'
    else:
        app.config['JWT_COOKIE_DOMAIN'] = 'localhost'

    jwt = JWTManager(app)
    #--

    return jwt

app = create_app()
jwt = create_jwt()

#handle crashes
@app.errorhandler(500)
def server_error(e):
    return jsonify(error=str(e)), 500

from flask_cors import CORS
CORS(app,  supports_credentials=True)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='localhost', port=port)
