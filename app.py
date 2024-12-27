from flask import Flask, jsonify
from scrap_script import ScrapTwitter  # Import the function from main.py
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route('/run-selenium', methods=['GET'])
def run_selenium():
    # Call the function from main.py
    result = ScrapTwitter()
    print("result from flask: ", result)
    return jsonify(result)  # Return the result as a JSON response

if __name__ == '__main__':
    app.run(debug=True)
