import os

from flask import Flask
from openai import OpenAI

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

KEY = "sk-proj-WKoMoUxcBoLAooeZW7q6T3BlbkFJqKSe48dOzJzbEfOv4aag"
#setup the openai api key

documents= SimpleDirectoryReader("data_temp").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

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