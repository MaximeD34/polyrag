
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

from flask_jwt_extended import jwt_required, get_jwt_identity

@user_routes.route('/user_infos', methods=['GET'])
@jwt_required()
def user_infos():
    
    current_user_id = get_jwt_identity()
    user = Users.query.filter_by(id=current_user_id).first()
    if user is None:
        return {"error": "User not found"}, 404
    else:
        return jsonify(username=user.username, email=user.email), 200
