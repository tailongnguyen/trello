from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_cors import CORS

import signal
import sys, os
import json 
import time

app = Flask(__name__)
CORS(app)
   
def exit_signal_handler(sig, frame):
    print('You pressed Ctrl+C.')
    sys.exit()

@app.route('/get-list', methods=['GET'])
def get_list():
    
    return jsonify(result=None)

@app.route('/', methods=['GET'])
def face_check_in():
    return render_template('index.html')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_signal_handler)
    app.run(port=5050, debug=False)
