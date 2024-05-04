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
#--

def create_app():
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
    #--

    #register the routes
    app.register_blueprint(user_routes)
    #--

    return app

app = create_app()

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)
