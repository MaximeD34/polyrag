#for openai
from openai import OpenAI
import openai
import os
openai.api_key = os.getenv("OPENAI_KEY")
#openai.api_key = "sk-proj-fRw4wXtVT1cIO3W8EHawT3BlbkFJkhsLrSm5bNE45Eh75GW2"
#--

#to create route blueprints
from flask import Blueprint, jsonify, request
#--

ai_routes = Blueprint('ai_routes', __name__)

#TODO : make the index persitent across deployments

#init: create a document object with all the files
from llama_index.core import StorageContext, load_index_from_storage, VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.vector_stores import MetadataFilters, FilterCondition, ExactMatchFilter, MetadataFilter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

from database import db
from models import Files



def getAuthorizedFilesFromList(user_id, filecodes):
    #This function returns as [Int] the filecodes the user has access to from the list of filecodes
    #If the user has access to all the files, it returns the list of filecodes
    #If the user has access to none of the files, it returns an empty list
    #If the user has access to some of the files, it returns the list of filecodes the user has access to

    authorized_files = []
    for filecode in filecodes:
        
        #check if the file exists
        file = Files.query.filter_by(id=filecode).first()
        if file is None:
            continue
        #if the file is private and the user is not the owner, ignore it
        if not file.is_public and file.user_id != user_id:
            continue
        authorized_files.append(filecode)
        
    return authorized_files

#to handle the jwt
from flask_jwt_extended import jwt_required, get_jwt_identity
#--

from models import EmbeddingStatus
from llama_index.core import PromptTemplate

@ai_routes.route('/query', methods=['POST'])
@jwt_required()
def query():

    #POST:
    #{
    #    "query" : String => the query,
    #    "filecodes" : [Int] => the filecodes of the files to search in (might be empty)
    #   "instructions" : String => the instructions for the query
        #}
    #The function verifies that the query is a string and that the filecodes is a list of integers
    #It then searches in the files with the given filecodes IF THE USER HAS ACCESS TO THEM (and ignore them if not)
    #If no filecodes are given, it searches in all the privates files the user has access to
    #If after filtering the user has no access to any file, it returns an empty response

    data = request.json
    if not isinstance(data, dict):
        return jsonify({"msg" : "Invalid request"}), 400
    query = data['query'] 
    instructions = data['instructions'] #the instructions for the query
    filecodes = data['filecodes']

    if instructions is None:
        instructions = "No specific constraints."
    
    if not isinstance(query, str):
        return jsonify({"msg" : "Invalid query. query should be a string"}), 400
    if not isinstance(filecodes, list) or not all(isinstance(code, int) for code in filecodes):
        return jsonify({"msg" : "Invalid filecodes. filecodes should be a list of integers"}), 400

    user_id = get_jwt_identity()

    #check if files are done embedding
    for filecode in filecodes:
        status = EmbeddingStatus.query.filter_by(file_id=filecode).first()
        if status is None or status.status != "done":
            return jsonify({"msg" : "Some files are not done embedding"}), 300


    authorized_files = getAuthorizedFilesFromList(user_id, filecodes)
    # print(authorized_files)

    if not authorized_files:
        return jsonify({"msg" : "No authorized files to search in"}), 300

    from embeddings_manager import getMergedIndexWithFileIds

    #global variable for the storage path
    storage_path = os.getenv('STORAGE_PATH', '/home/maxime/PolyRag/backend/../local_test_persistent_storage/')
    #
    index, skippedFiles = getMergedIndexWithFileIds(storage_path, authorized_files)

    query_engine = index.as_query_engine(response_mode="tree_summarize", similarity_top_k= 1 + 1 + len(authorized_files)-len(skippedFiles))

    

    template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "The user would like you to respond with the following constraints below. \n"
    + instructions +
    "\n---------------------\n"
    "Given this information and the constraints, please answer the question : {query_str}\."
    )
    qa_template = PromptTemplate(template)
    query_engine.update_prompts( {"response_synthesizer:summary_template": qa_template})
    response = query_engine.query(query)
     
    # Convert NodeWithScore objects to JSON
    source_nodes = [node.to_dict() for node in response.source_nodes]

    json = {
        "unauthorized_files" : [filecode for filecode in filecodes if filecode not in authorized_files], #the files the user doesn't have access to
        "corrupted_files" : skippedFiles,
        "response" : response.response,
        "metadata" : response.metadata,
        "source_nodes" : source_nodes
    }
    
    return json , 200
