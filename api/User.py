import dbs_worker
import uuid
import json
import datetime
from LiveFocusModes import LiveFocusMode
import requests
import constants
from apns2.credentials import TokenCredentials
from apns2.client import APNsClient
from apns2.payload import Payload
import ssl
import subprocess
class User:
    user_data = None
    authenticated = False
    def __init__(self, user_id, device_id):
        self.user_data = dbs_worker.get_user_by_id(user_id)
        self.user_id = user_id
        if self.get_data_as_dict()['data'] != None:
            if device_id in self.get_data_as_dict()['data']['devices']:
                self.authenticated = True
        if self.get_data_as_dict()['mobile_devices'] != None:
            if device_id in self.get_data_as_dict()['mobile_devices']['phone_ids']:
                self.authenticated = True
        
    
    @classmethod
    def create_user(cls, name,privacy_status, device_id):

        user_id = dbs_worker.create_user(name,privacy_status, {'devices': [device_id],"share_code":str(uuid.uuid4())})
        print(user_id)
        user = cls(user_id, device_id)
        return user

    def get_data_as_dict(self):
        dbs_worker.get_user_by_id(self.user_id)
        return {
            'user_id': self.user_data[0],
            'name': self.user_data[1],
            'email': self.user_data[2],
            'date_created': self.user_data[3],
            'privacy_status': self.user_data[4],
            'last_login': self.user_data[5],
            'data': self.user_data[6],
            'mobile_devices': self.user_data[7],
        }     
    def set_display_name(self, name):
        dbs_worker.set_user_display_name(self.user_id, name)
        self.user_data = dbs_worker.get_user_by_id(self.user_id)
        return True 
    def set_privacy_status(self, status):
        dbs_worker.set_user_privacy_status(self.user_id, status)
        self.user_data = dbs_worker.get_user_by_id(self.user_id)
        return True
    def add_friend(self, friend_id):
        cur_data = self.get_data_as_dict()['data']
        if 'friends' in cur_data:
            if friend_id in cur_data['friends']:
                pass
            else:
                cur_data['friends'] = [friend_id, *cur_data['friends']]
                print('added friend')
                print(cur_data['friends'])
        else:
            cur_data['friends'] = [friend_id]
        dbs_worker.set_user_data(self.user_id, cur_data)
        self.user_data = dbs_worker.get_user_by_id(self.user_id)
        return True
    def get_friend_data(self):
        friend_data = []
        if 'friends' in self.get_data_as_dict()['data']:
            for friend in self.get_data_as_dict()['data']['friends']:
                friend_data.append(User(friend,None).get_friend_sharable_data())
        else:
            return None
        cur_data = self.get_data_as_dict()['data']
        cur_data['friends_data'] = {'data':friend_data,'last_updated':dbs_worker.get_current_time()}
        dbs_worker.set_user_data(self.user_id, cur_data)    
        return friend_data
    
    def get_friend_sharable_data(self):
        return {
            'user_id': self.user_data[0],
            'name': self.user_data[1],
            'data': self.user_data[6]['share_data'] if 'share_data' in self.user_data[6] else None
        }
    
    def save_live_sharable_data(self, data):
        cur_data = self.get_data_as_dict()['data']
        if 'share_data' in cur_data:
            cur_data['share_data']['live'] = data
        else:
            cur_data['share_data'] = {'live': data}
        dbs_worker.set_user_data(self.user_id, cur_data)
    def save_leaderboard_data(self, data,time,expiry):
        cur_data = self.get_data_as_dict()['data']
        if 'share_data' in cur_data:
            if 'leaderboard' in cur_data['share_data']:
                cur_data['share_data']['leaderboard'][time] = {'data':data,'last_updated':dbs_worker.get_current_time(),'expiry':dbs_worker.set_time_in_format(datetime.datetime.now() + datetime.timedelta(seconds=expiry))}
            else:
                cur_data['share_data']['leaderboard'] = {time:{'data':data,'last_updated':dbs_worker.get_current_time(),'expiry':dbs_worker.set_time_in_format(datetime.datetime.now() + datetime.timedelta(seconds=expiry))}}

        else:
            cur_data['share_data'] = {'leaderboard':{time:{'data':data,'last_updated':dbs_worker.get_current_time(),'expiry':dbs_worker.set_time_in_format(datetime.datetime.now() + datetime.timedelta(seconds=expiry))}}}

        dbs_worker.set_user_data(self.user_id, cur_data)

    def add_live_focus_mode_request(self, data):
        cur_data = self.get_data_as_dict()['data']
        if 'focus_mode_requests' in cur_data:
            if data in cur_data['focus_mode_requests']:
                pass
            else:
                cur_data['focus_mode_requests'].append(data)
        else:
            cur_data['focus_mode_requests'] = [data]
        dbs_worker.set_user_data(self.user_id, cur_data)
    
    def get_live_focus_mode_requests(self):
        cur_data = self.get_data_as_dict()['data']
        if 'focus_mode_requests' in cur_data:
            return cur_data['focus_mode_requests']
        else:
            return []
    
    def get_current_live_focus_mode(self):
        cur_data = self.get_data_as_dict()['data']
        if 'current_live_focus_mode' in cur_data:
            if cur_data['current_live_focus_mode'] == None:
                return None
            return LiveFocusMode(cur_data['current_live_focus_mode'])
        else:
            return None
    
    def remove_live_focus_mode_request(self, id):
        cur_data = self.get_data_as_dict()['data']
        if 'focus_mode_requests' in cur_data:
            cur_data['focus_mode_requests'].remove(id)
        else:
            return None
        dbs_worker.set_user_data(self.user_id, cur_data)

    def add_current_live_focus_mode(self,id):
        cur_data = self.get_data_as_dict()['data']
        cur_data['current_live_focus_mode'] = id
        dbs_worker.set_user_data(self.user_id, cur_data)
    def remove_current_live_focus_mode(self):
        cur_data = self.get_data_as_dict()['data']
        cur_data['current_live_focus_mode'] = None
        dbs_worker.set_user_data(self.user_id, cur_data)

    def add_phone_number(self, phone_number):
        cur_data = self.get_data_as_dict()['mobile_devices']
        if cur_data == None or cur_data == {}:
            cur_data = {
                'phone_ids': [phone_number],
                'settings': {

                }
            }
        else:
            if 'phone_ids' in cur_data:
                if phone_number in cur_data['phone_ids']:
                    pass
                else:
                    cur_data['phone_ids'] = [phone_number, *cur_data['phone_ids']]
        dbs_worker.set_user_mobile_devices(self.user_id, cur_data)
    def save_current_focus_mode(self,duration,name,type,id):

        cur_data = self.get_data_as_dict()['data']
        cur_data['current_focus_mode'] = {'duration':duration,'name':name,'type':type,'start_time':dbs_worker.get_current_time(),'id':id,"active":True}
        dbs_worker.set_user_data(self.user_id, cur_data)
    def stop_focus_mode(self):
        cur_data = self.get_data_as_dict()['data']
        if 'current_focus_mode' in cur_data:
            cur_data['current_focus_mode']['active'] = False
        dbs_worker.set_user_data(self.user_id, cur_data)
    def send_notification_to_phone(self,title,subtitle,body):
#         curl -v \
#   --header "authorization: bearer ${AUTHENTICATION_TOKEN}" \
#   --header "apns-topic: com.shoryamalani.fixate" \
#   --header "apns-push-type: alert" \
#   --header "apns-priority: 5" \
#   --header "apns-expiration: 0" \
#   --data '{"aps":{"alert":{"title":"Focus Title","subtitle":"Start a focus mode","body":"Click on the notification to continue the focus mode on your phone"}}}' \
#   --http2  https://api.development.push.apple.com:443/3/device/
        phone_ids = self.get_data_as_dict()['mobile_devices']['phone_ids']
        device_ids = []
        for phone_id in phone_ids:
            get_phone_data = dbs_worker.get_phone_data(phone_id)
            if get_phone_data[6] != None:
                device_ids.append(get_phone_data[6])
                # Create the APNs client
        # Set the appropriate APNs server endpoint (sandbox for development, production for live app)
        # Create a notification payload
        
        # Send the notification
        print(constants.CERT_FILE_PATH)
        import os
        print(os.path.exists(constants.CERT_FILE_PATH))
        print(constants.AUTH_FILE_PATH)
        print(os.path.exists(constants.AUTH_FILE_PATH))
        for device_id in device_ids:
            curl_command = [
    ["curl -v","--cert", constants.AUTH_FILE_PATH,],
    ["--cert-type", "DER",],
    ["--key", constants.CERT_FILE_PATH],
    ["--key-type", "PEM"],
    ["--header", '"apns-topic: com.shoryamalani.fixate"',],
    ["--header", '"apns-push-type: alert"',],
    ["--header", '"apns-priority: 5"'],
    ["--header", '"apns-expiration: 0"'],
    [ "--data", '\'{"aps":{"alert":{"title":"'+title+'","subtitle":"'+subtitle+'","body":"'+body+'"}}}\'',],
    ["--http2", "https://api.development.push.apple.com:443/3/device/" + device_id]
]

            final_command = ""
            for line in curl_command:
                final_command += " ".join(line) + " \\\n"

            try:
                subprocess.run(final_command, shell=True)
            except subprocess.CalledProcessError as e:
                print("Error executing curl command:", e)
            pass
        # Close the APNs client
    
    def is_running_focus_mode(self):
        cur_data = self.get_data_as_dict()['data']
        if 'current_focus_mode' in cur_data:
            if cur_data['current_focus_mode'] == None:
                return False
            else:
                if dbs_worker.get_time_from_format(cur_data['current_focus_mode']['start_time']) + datetime.timedelta(seconds=cur_data['current_focus_mode']['duration']) < datetime.datetime.now():
                    return cur_data['current_focus_mode']
                else:
                    return False
        else:
            return False
    @staticmethod
    def get_leaderboard_data():
        # dbs_worker.get_all_public_users_share_data() # format is user_id, name, data
        data  = dbs_worker.get_all_public_users_share_data()
        print(data)
        now = datetime.datetime.now()
        final_data = {'expire_time': datetime.datetime.now()+ datetime.timedelta(seconds=180),'data':{}}
        for user in data:
            cur_data = user[2]
            if 'share_data' in  cur_data:
                print(cur_data['share_data'].keys())
                if 'leaderboard' in cur_data['share_data']:
                    print(cur_data['share_data']['leaderboard'])
                    for time in cur_data['share_data']['leaderboard']:
                        if dbs_worker.get_time_from_format(cur_data['share_data']['leaderboard'][time]['expiry']) > now:
                            if user[0] in final_data['data']:
                                final_data['data'][user[0]][time] = cur_data['share_data']['leaderboard'][time]
                            else:
                                final_data['data'][user[0]] = {time:cur_data['share_data']['leaderboard'][time], 'name':user[1]}
        return final_data
    
    @staticmethod
    def authenticate_friend_code(user_name,share_code):
        users = dbs_worker.get_users_by_name(user_name)
        for user in users:
            if user[6] != None:
                if user[6]['share_code'] == share_code:
                    return user[0]
        return None
    
