from flask import Blueprint, jsonify, request, g
import dbs_worker
import base64
import random
from User import User
mobileApp = Blueprint('mobileApp', __name__)

@mobileApp.route('/addMobileDeviceAndLogin', methods=['POST'])
def addMobileDeviceAndLogin():
    request_data = request.get_json()
    if request_data is None:
        return jsonify({'status': 'error'}), 400
    device_id = request_data.get('device_id')
    if device_id is None:
        return jsonify({'status': 'error'}), 400
    cur = dbs_worker.check_if_device_id_exists(device_id)
    if cur is None:
        dbs_worker.add_mobile_device(device_id)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'success'})

@mobileApp.route('/addMobileNotificationCode', methods=['POST'])
def addMobileNotificationCode():
    request_data = request.get_json()
    if request_data is None:
        return jsonify({'status': 'error'}), 400
    device_id = request_data.get('device_id')
    notification_code = request_data.get('notification_code')

    if device_id is None or notification_code is None:
        return jsonify({'status': 'error'}), 400
    cur = dbs_worker.check_if_device_id_exists(device_id)
    if cur is None:
        return jsonify({'status': 'error'}), 400
    else:
        d = base64.b64decode(notification_code)
        d1=''.join(['{:02x}'.format(i) for i in d])
        dbs_worker.add_mobile_notification_code(device_id, d1)
        return jsonify({'status': 'success'})
@mobileApp.route('/getMobileConnectCode', methods=['GET','POST'])
def getPhoneConnectCode():
    request_data = request.get_json()
    if request_data is None:
        return jsonify({'status': 'error'}), 400
    device_id = request_data.get('device_id')
    if device_id is None:
        return jsonify({'status': 'error'}), 400
    cur = dbs_worker.check_if_device_id_exists(device_id)
    if cur is None:
        return jsonify({'status': 'error'}), 400
    else:
        connect_code = random.randint(100000, 999999)
        dbs_worker.add_mobile_connect_code(device_id, connect_code)
        return jsonify({'status': 'success', 'connect_code': connect_code})

@mobileApp.route('/isFocusModeRunning', methods=['GET','POST'])
def isFocusModeRunning():
    request_data = request.get_json()
    if request_data is None:
        return jsonify({'status': 'error'}), 400
    device_id = request_data.get('device_id')
    if device_id is None:
        return jsonify({'status': 'error'}), 400
    userId = dbs_worker.get_user_id_from_device_id(device_id)
    if userId is None:
        return jsonify({'status': 'error'}), 400
    focus_mode = User(userId,device_id).is_running_focus_mode()
    if focus_mode is None:
       return jsonify({'status': 'error'}), 400 
    else:
        return jsonify({'status': 'success', 'focus_mode_name': focus_mode['name'],'focus_mode_duration': focus_mode['duration'],'focus_mode_type': focus_mode['type'],'focus_mode_start_time': focus_mode['start_time']})