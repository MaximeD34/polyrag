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

def create_app():
    app = Flask(__name__)
    print("app was created")
    return app

app = create_app()