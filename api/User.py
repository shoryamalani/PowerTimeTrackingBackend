import dbs_worker
import uuid
import datetime
class User:
    user_data = None
    authenticated = False
    def __init__(self, user_id, device_id):
       self.user_data = dbs_worker.get_user_by_id(user_id)
       self.user_id = user_id
       if self.get_data_as_dict()['data'] != None:
           if device_id in self.get_data_as_dict()['data']['devices']:
               self.authenticated = True
    
    @classmethod
    def create_user(cls, name,privacy_status, device_id):

        user_id = dbs_worker.create_user(name,privacy_status, {'devices': [device_id],"share_code":str(uuid.uuid4())})
        print(user_id)
        user = cls(user_id, device_id)
        return user

    def get_data_as_dict(self):
        return {
            'user_id': self.user_data[0],
            'name': self.user_data[1],
            'email': self.user_data[2],
            'date_created': self.user_data[3],
            'privacy_status': self.user_data[4],
            'last_login': self.user_data[5],
            'data': self.user_data[6],
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
            cur_data['friends'].append(friend_id)
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
    @staticmethod
    def get_leaderboard_data():
        # dbs_worker.get_all_public_users_share_data() # format is user_id, name, data
        data  = dbs_worker.get_all_public_users_share_data()
        print(data)
        now = dbs_worker.get_current_time()
        final_data = {'expire_time': datetime.datetime.now()+ datetime.timedelta(seconds=180),'data':[]}
        for user in data:
            if 'share_data' in  user[2]:
                if 'leaderboard' in user[2]['share_data']:
                    for time in user[2]['share_data']['leaderboard']:
                        if user[2]['share_data']['leaderboard'][time]['expiry'] < now:
                            if user[0] in final_data['data']:
                                final_data['data'][user[0]][time] = user[2]['share_data']['leaderboard'][time]
                            else:
                                final_data['data'][user[0]] = {time:user[2]['share_data']['leaderboard'][time], 'name':user[1]}
        return final_data
    
    @staticmethod
    def authenticate_friend_code(user_name,share_code):
        users = dbs_worker.get_users_by_name(user_name)
        for user in users:
            if user[6] != None:
                if user[6]['share_code'] == share_code:
                    return user[0]
        return None
    
