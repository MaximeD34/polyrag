import os

from flask import Flask
from openai import OpenAI

import openai
openai.api_key = 'sk-proj-WKoMoUxcBoLAooeZW7q6T3BlbkFJqKSe48dOzJzbEfOv4aag'

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

print("-----------------")
print("Starting the server")

#setup the openai api key

print("loading the data...")
documents= SimpleDirectoryReader("data_temp").load_data()
print("data loaded")
print("creating the index...")
index = VectorStoreIndex.from_documents(documents)
print("index created")
print("creating the query engine...")
query_engine = index.as_query_engine()
print("query engine created")

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

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)