import os

from flask import Flask

#for the file transfer
from flask import Flask, request
from werkzeug.utils import secure_filename
#--

#for openai
from openai import OpenAI
import openai
openai.api_key = os.getenv("OPENAI_KEY")
#--

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

import time


app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/<name>')
def hello_name(name):
    return 'Hello {}! new version'.format(name)

@app.route('/openai')
#returns a json with the nodes datas
def openai():
    response = query_engine.query("What are the steps to cleaning the print cartridge contacts ?")
    
    nodes = {node_dict['node']['id_']: {k: v for k, v in node_dict['node'].items() if k != 'id_'} 
         for node in response.source_nodes 
         for node_dict in [node.to_dict()]}
    
    return nodes 

@app.route('/upload', methods=['POST'])
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

@app.route('/list_files')
def list_files():
    try:
        storage_path = os.getenv('STORAGE_PATH', '../test_storage')
        files = os.listdir(storage_path)
        return '<br>'.join(files)
    except Exception as e:
        return str(e)

@app.route('/debug', methods=['GET'])
def debug():
    try:
        directories = os.listdir('/app')
    except Exception as e:
        directories = str(e)
    return {"directories": directories}, 200

if __name__ == '__main__':

    print("-----------------")
    print("Starting the server")

    print(f"{time.ctime()} - loading the data...")
    documents= SimpleDirectoryReader("data_temp").load_data()
    print(f"{time.ctime()} - data loaded")

    print(f"{time.ctime()} - creating the index...")
    index = VectorStoreIndex.from_documents(documents)
    print(f"{time.ctime()} - index created")

    print(f"{time.ctime()} - creating the query engine...")
    query_engine = index.as_query_engine()
    print(f"{time.ctime()} - query engine created")

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)

    