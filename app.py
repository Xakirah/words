from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)

cxn_str = 'mongodb+srv://harisd:harisqwe23@cluster0.keidjvf.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(cxn_str)
db = client.dbsparta_plus

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({  
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = "888aee72-fd1e-485f-95d3-552f62c3204f" # Get the API key from an environment variable
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        definitions = response.json()

        if not definitions:
            return render_template('error.html', msg=f'Could not find "{keyword}"', suggestions=None)

        if isinstance(definitions[0], str):
            suggestions = definitions
            return render_template('error.html', msg=f'Could not find "{keyword}"', suggestions=suggestions)

        status = request.args.get('status_give', 'new')
        return render_template(
            'detail.html',
            word=keyword,
            definitions=definitions,
            status=status
        )

    except requests.exceptions.RequestException as e:
        return render_template('error.html', msg=f'Error fetching data for {keyword}: {str(e)}', suggestions=None)

    except ValueError as e:
        return render_template('error.html', msg=f'Error parsing data for {keyword}: {str(e)}', suggestions=None)


@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%d %m %Y')
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id')),
        })
    return jsonify({
        'result': 'success',
        'examples': examples,
    })


@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    json_data = request.get_json()
    word = json_data.get('word')
    example = json_data.get('example')
    doc = {
        'word': word,
        'example': example,
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'Your example, "{example}", for the word "{word}", was saved.'
    })

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    json_data = request.get_json()
    id = json_data.get('id')
    word = json_data.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'The example for word "{word}" was deleted.'
    })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
