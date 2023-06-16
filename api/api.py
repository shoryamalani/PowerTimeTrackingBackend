import time
from flask import Flask, jsonify, request , redirect, url_for, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import dbs_worker
import os
import json
from functools import wraps
from flask import g, request, redirect, url_for
from flask_session import Session
from User import User
import uuid
app = Flask(__name__, static_folder='../build', static_url_path='/')
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('user_id', None)
        device_id = request.headers.get('device_id', None)

        if user_id is None or device_id is None:
            print(request.headers)
            print("bad request")
            print("user_id: " + str(user_id))
            print("device_id: " + str(device_id))
            return jsonify({'error': 'bad request'}), 400
        user = User(user_id, device_id)
        if user.authenticated:
            print("authenticated")
            g.user = user
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'not authenticated'}), 401
    return decorated_function

def require_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'bad request'}), 400
        return f(*args, **kwargs)
    return decorated_function


@app.errorhandler(404)
def not_found(e):
    print(e)
    return jsonify({"status": "not found"}), 404

@app.route('/')
def index():
    return jsonify({"status": "ok"}), 200

@app.route('/api/createUser', methods=['POST'])
def createUser():
    j = request.get_json()
    user = User.create_user(j.get('name'),j.get('privacy_level', None),j.get('device_id', None))
    return jsonify({'user_id': user.get_data_as_dict()['user_id']})

@app.route('/api/getUser', methods=['GET'])
@authenticate
def getUser():
    return jsonify({'user_data':g.user.get_data_as_dict()})

@app.route('/api/changePrivacy', methods=['POST'])
@authenticate
@require_json
def changePrivacy():
    j = request.get_json()
    user:User = g.user
    user.set_privacy_status(j.get('privacy_level'))
    print("Changing privacy to " + j.get('privacy_level'))
    return jsonify({'success': True})

@app.route('/api/createDeviceId', methods=['GET'])
def createDeviceId():
    id = str(uuid.uuid4())
    return jsonify({'device_id': id})

@app.route('/api/setDisplayName', methods=['POST'])
@authenticate
def setDisplayName():
    j = request.get_json()
    if j is None:
        return jsonify({'error': 'bad request'}), 400
    user:User = g.user
    user.set_display_name(j.get('display_name'))
    print("Changing name to " + j.get('display_name'))
    return jsonify({'success': True})

@app.route('/api/addFriend', methods=['POST'])
@authenticate
def addFriend():
    j = request.get_json()
    if j is None:
        return jsonify({'error': 'bad request'}), 400
    user:User = g.user
    friend_user_id  = User.authenticate_friend_code(j.get('friend_name'),j.get('friend_share_code'))
    print("Adding friend " + str(friend_user_id))
    if friend_user_id is None:
        return jsonify({'error': 'bad friend code'}), 400
    user.add_friend(friend_user_id)
    print("Added friend " + str(friend_user_id))
    user.get_friend_data()
    return jsonify({'success': friend_user_id})

@app.route('/api/getFriendData', methods=['GET'])
@authenticate
def getFriendData():
    user:User = g.user
    return jsonify({'friend_data': user.get_friend_data()})

@app.route('/api/saveLiveSharableData', methods=['POST'])
@authenticate
@require_json
def saveLiveSharableData():
    j = request.get_json()
    user:User = g.user
    user.save_live_sharable_data(j.get('live_data'))
    print("Saving live data")
    return jsonify({'success': True})



if __name__ == "__main__":
    app.run(port=5008, debug=True)