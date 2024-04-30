import os

from flask import Flask
from openai import OpenAI


app = Flask(__name__)

#setup the openai api key
KEY = "sk-proj-WKoMoUxcBoLAooeZW7q6T3BlbkFJqKSe48dOzJzbEfOv4aag"
client = OpenAI(api_key=KEY)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/<name>')
def hello_name(name):
    return 'Hello {}! new version'.format(name)

@app.route('/openai')
def openai():
    query = "What is the capital of France?"
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant, answer the following question."},
            {"role": "user", "content": query}
        ]
    )
    return completion.choices[0].message.content


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)