#for the file upload
from werkzeug.utils import secure_filename
#--

#for openai
from openai import OpenAI
import openai
import os
openai.api_key = os.getenv("OPENAI_KEY")
#openai.api_key = "sk-proj-fRw4wXtVT1cIO3W8EHawT3BlbkFJkhsLrSm5bNE45Eh75GW2"
#--

#for llama
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
#--

#TODO change the path to the data
documents= SimpleDirectoryReader("data_temp").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
#--

#to create route blueprints
from flask import Blueprint, jsonify, request
#--

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/')
def hello():
    return 'Hello World!'

@user_routes.route('/<name>')
def hello_name(name):
    return 'Hello {}! new version'.format(name)

@user_routes.route('/openai')
def openai():
    try:
        response = query_engine.query("What are the steps to cleaning the print cartridge contacts ?")
        
        nodes = {node_dict['node']['id_']: {k: v for k, v in node_dict['node'].items() if k != 'id_'} 
            for node in response.source_nodes 
            for node_dict in [node.to_dict()]}
        
        return nodes

    except Exception as e:
        return str(e)

@user_routes.route('/upload', methods=['POST'])
def upload_file():

    storage_path = os.getenv('STORAGE_PATH', '../test_storage')

    if 'file' not in request.files:
        return {"error": "No file part"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(storage_path, filename))

    return {"message": "File uploaded successfully"}, 200

@user_routes.route('/list_files')
def list_files():
    try:
        storage_path = os.getenv('STORAGE_PATH', '../test_storage')
        files = os.listdir(storage_path)
        return '<br>'.join(files)
    except Exception as e:
        return str(e)

@user_routes.route('/debug', methods=['GET'])
def debug():
    try:
        directories = os.listdir('/app')
    except Exception as e:
        directories = str(e)
    return {"directories": directories}, 200

from database import db
from sqlalchemy import inspect
@user_routes.route('/db_selectAll/<table_name>', methods=['GET'])
def db_selectAll(table_name):
    inspector = inspect(db.engine)

    if table_name in inspector.get_table_names():
        table = db.Model.metadata.tables[table_name]
        query = db.session.query(table).all()
        return jsonify([row._asdict() for row in query])
    else:
        return {"error": "Table not found"}, 404

from models import Users
from werkzeug.security import generate_password_hash, check_password_hash
#params : username, password, email
@user_routes.route('/create_user', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        username = data['username']
        email = data['email']
        hashed_password = generate_password_hash(data['password'])

        user = Users(username=username, email=email, hashed_password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully"}, 200
    except Exception as e:
        return str(e), 400
    
from flask_jwt_extended import create_access_token, create_refresh_token
@user_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', None)
    password = data.get('password', None)

    user = Users.query.filter_by(email=email).first()
    if user and check_password_hash(user.hashed_password, password):
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    return jsonify({"msg": "Bad username or password"}), 401

from flask_jwt_extended import jwt_required, get_jwt_identity

@user_routes.route('/user_infos', methods=['GET'])
@jwt_required()
def user_infos():
    current_user = get_jwt_identity()
    user = Users.query.filter_by(email=current_user).first()
    return jsonify(username=user.username, email=user.email), 200
