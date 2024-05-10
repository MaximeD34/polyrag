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

print("Starting the indexing...")
storage_path = os.getenv('STORAGE_PATH', '/home/maxime/PolyRag/backend/../test_storage')
metadata_fn = lambda filename: {'file_name' : filename}

#init the documents
documents = SimpleDirectoryReader(input_dir=storage_path, 
                                  recursive=True,
                                  file_metadata=metadata_fn).load_data()

#create the index
index = VectorStoreIndex.from_documents(documents=documents)
print("... End of indexing")
#----

print(documents[0].metadata)

from flask_jwt_extended import jwt_required, get_jwt_identity

@ai_routes.route('/query', methods=['POST'])
@jwt_required()
def query():
    data = request.get_json()
    if 'query' not in data:
        return {"error": "No query part"}, 400
    if 'private_filecodes' not in data:
        return {"error": "No filecode part"}, 400

    query = data['query']
    private_filecodes = data.get('private_filecodes', [])
    #check if query is a string
    if not isinstance(query, str):
        return {"error": "Query should be a string"}, 400
    #check if private_filenames is a list of integers:
    if not isinstance(private_filecodes, list) or not all(isinstance(i, int) for i in private_filecodes):
        return {"error": "private_filecodes should be a list of integers"}, 400
    
    user_id = get_jwt_identity()

    private_filecodes = [os.path.join(storage_path, str(user_id), str(filecode)) for filecode in private_filecodes]

    print(private_filecodes)
    #TODO we need to put the actual name of the file, not just the code

    filters = [
        MetadataFilter(
            key='file_name',
            value=fname
        )
        for fname in private_filecodes
    ]
    filters = MetadataFilters(filters=filters, condition='or')
    query_engine = index.as_query_engine(filters=filters)

    response = query_engine.query(query)

    print(response)

    # Convert NodeWithScore objects to JSON
    source_nodes = [node.to_dict() for node in response.source_nodes]

    json = {
        "response" : response.response,
        "metadata" : response.metadata,
        "source_nodes" : source_nodes
    }
    
    return json , 200