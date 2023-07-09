import time
from flask import Flask, jsonify, request , redirect, url_for, request, session
from flask_cors import CORS
import dbs_worker
import os
import json
from functools import wraps
from flask import g, request, redirect, url_for
from flask_session import Session
from User import User
from LiveFocusModes import LiveFocusMode
import uuid
import eventlet
app = Flask(__name__, static_folder='../build', static_url_path='/')
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
CORS(app)

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
    dbs_worker.add_user_to_users_number()
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
    User(friend_user_id,None).add_friend(int(user.user_id))
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

@app.route('/api/saveLeaderboardData', methods=['POST'])
@authenticate
@require_json
def saveLeaderboardData():
    j = request.get_json()
    user:User = g.user
    expiry = 1000000
    if j.get('timing') == 'daily':
        expiry = 86400
    elif j.get('timing') == 'weekly':
        expiry = 604800
    elif j.get('timing') == 'monthly':
        expiry = 2592000
    user.save_leaderboard_data(j.get('leaderboard_data'),j.get('timing'),expiry)
    print("Saving leaderboard data")
    return jsonify({'success': True})

@app.route('/api/getLeaderboardData', methods=['GET'])
def getLeaderboardData():
    return jsonify({'leaderboard_data': User.get_leaderboard_data()})

# live focus mode requests
@app.route("/api/getLiveFocusModeData", methods=['GET'])
@authenticate
def getLiveFocusModeData():
    user:User = g.user
    requests = user.get_live_focus_mode_requests()
    final_requests = []
    for request in requests:
        focus = LiveFocusMode(request)
        if focus.is_active() != True:
            User(request,None).remove_live_focus_mode_request(focus.id)
        else:
            final_requests.append(focus.get_data_as_dictionary())
    focus = user.get_current_live_focus_mode()
    if focus != None:
        if focus.is_active() != True:
            user.remove_current_live_focus_mode()
    return jsonify({'data': None if focus == None else focus.get_data_as_dictionary(),'requests': final_requests, 'status': 'success'})

@app.route('/api/createLiveFocusMode', methods=['POST'])
@authenticate
@require_json
def createLiveFocusMode():
    j = request.get_json()
    user:User = g.user
    live_focus_mode = LiveFocusMode.create_live_focus_mode(j.get('name'),user.user_id)
    user.add_current_live_focus_mode(live_focus_mode.id)
    return jsonify({'status': 'success'})

@app.route('/api/getLiveFocusModeRequests', methods=['GET'])
@authenticate
def getLiveFocusModeRequests():
    user:User = g.user

    return jsonify({'live_focus_mode_requests': user.get_live_focus_mode_requests()})

@app.route('/api/updateLiveFocusMode', methods=['POST'])
@authenticate
@require_json
def updateLiveFocusMode():
    j = request.get_json()
    user:User = g.user
    print("Updating live focus mode")
    focus = user.get_current_live_focus_mode()
    if focus == None:
        return jsonify({'error': 'not active'}), 400
    try:
        if not focus.is_active():
            return jsonify({'error': 'not active'}), 200
    except:
        return jsonify({'error': 'not active'}), 200
    focus.update_user_data(user.user_id,j.get('data'))
    return jsonify({'data': focus.get_data_as_dictionary()})

@app.route('/api/addLiveFocusModeMember', methods=['POST'])
@authenticate
@require_json
def addLiveFocusModeMember():
    j = request.get_json()
    user:User = g.user
    focus = user.get_current_live_focus_mode()
    focus.add_member(j.get('user_id'))
    User(j.get('user_id'),None).add_live_focus_mode_request(user.get_current_live_focus_mode().id)
    return jsonify({'data': focus.get_data_as_dictionary()})

@app.route('/api/inviteToLiveFocusMode', methods=['POST'])
@authenticate
@require_json
def inviteLiveFocusMode():
    j = request.get_json()
    user:User = g.user
    focus = user.get_current_live_focus_mode()
    if focus == None:
        return jsonify({'error': 'not active'}), 400
    focus.add_invited_member(j.get('user_id'))
    User(j.get('user_id'),None).add_live_focus_mode_request(user.get_current_live_focus_mode().id)
    return jsonify({'data': focus.get_data_as_dictionary()})
@app.route('/api/joinLiveFocusMode', methods=['POST'])
@authenticate
@require_json
def joinLiveFocusMode():
    j = request.get_json()
    user:User = g.user
    focus = LiveFocusMode(j.get('live_focus_mode_id'))
    focus.add_member(user.user_id)
    user.add_current_live_focus_mode(focus.id)
    user.remove_live_focus_mode_request(focus.id)
    return jsonify({'data': focus.get_data_as_dictionary()})
@app.route('/api/leaveLiveFocusMode', methods=['POST'])
@authenticate
def leaveLiveFocusMode():
    user:User = g.user
    focus = user.get_current_live_focus_mode()
    focus.remove_member(user.user_id)
    user.remove_current_live_focus_mode()
    return jsonify({'success': True})

@app.route('/api/endLiveFocusMode', methods=['POST'])
@authenticate
def endLiveFocusMode():
    user:User = g.user
    focus = user.get_current_live_focus_mode()
    if focus == None:
        return jsonify({'error': 'not active'}), 400
    focus.deactivate()
    user.remove_current_live_focus_mode()
    return jsonify({'success': True})


if __name__ == "__main__":
    app.run(port=5008, debug=True)