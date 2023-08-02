from flask import Blueprint, jsonify, request, g
import dbs_worker
mobileApp = Blueprint('mobileApp', __name__)

@mobileApp.route('/addMobileDeviceAndLogin', methods=['GET'])
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

