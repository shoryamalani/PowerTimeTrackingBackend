import dbs_worker
import datetime

class LiveFocusMode:
    data = None
    def __init__(self,id):
        self.id = id
        self.data = dbs_worker.get_live_focus_modes_by_id(id)
    
    def get_data_as_dictionary(self):
        return {
            'id': self.data[0],
            'owner_id': self.data[2]['owner_id'],
            'name': self.data[1],
            'members': self.data[2]['members'],
            'invited_members': self.data[2]['invited_members'],
            'member_names': self.data[2]['member_names'],
            'active_members': self.data[2]['active_members'],
            'data': self.data[2]['data'],
            'active': self.data[2]['active'],
            'owner_name': self.data[2]['owner_name'],
        }
    
    @classmethod
    def create_live_focus_mode(cls,name,owner_id):
        data = {
            'owner_id': owner_id,
            'owner_name': dbs_worker.get_user_by_id(owner_id)[1],
            'members': [owner_id],
            'member_names': {
                owner_id: dbs_worker.get_user_by_id(owner_id)[1]
            },
            'invited_members': [],
            'active_members': {
                owner_id: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            'data': {
                'time_data':{
                    owner_id: []
                },
                'seconds': {
                    owner_id : {
                        'focused': 0,
                        'unfocused': 0
                    }
                }
            },
            'active': True,
        }
        return cls(dbs_worker.create_live_focus_mode(name,data))
    
    def add_member(self,user_id):
        data = self.get_data_as_dictionary()
        data['members'].append(str(user_id))
        data['invited_members'].remove(int(user_id))
        data['active_members'][user_id] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['member_names'][user_id] = dbs_worker.get_user_by_id(user_id)[1]
        data['data']['time_data'][user_id] = []
        data['data']['seconds'][user_id] = {'focused': 0, 'unfocused': 0}
        dbs_worker.set_live_focus_mode_data(self.id,data) 
    
    def update_data(self,user_id,data):
        if self.get_data_as_dictionary()['owner_id'] == user_id:
            dbs_worker.set_live_focus_mode_data(self.id,data)
    
    def remove_member(self,user_id):
        data = self.get_data_as_dictionary()
        data['members'].remove(user_id)
        dbs_worker.set_live_focus_mode_data(self.id,data)
    
    def add_invited_member(self,user_id):
        data = self.get_data_as_dictionary()
        data['invited_members'].append(user_id)
        dbs_worker.set_live_focus_mode_data(self.id,data)
    
    def update_user_data(self,user_id,update_data):
        print("update user data")
        if self.is_active() == False:
            return False
        print("is active")
        data = self.get_data_as_dictionary()
        user_id = str(user_id)
        data['data']['time_data'][user_id] = update_data['focused']
        if update_data['focused']:
            data['data']['seconds'][user_id]['focused'] += update_data['seconds']
        else:
            data['data']['seconds'][user_id]['unfocused'] += update_data['seconds']
        data['active_members'][user_id] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dbs_worker.set_live_focus_mode_data(self.id,data)
    def is_active(self):
        if not self.get_data_as_dictionary()['active']:
            return False
        active = False
        for member in self.get_data_as_dictionary()['active_members']:
            if datetime.datetime.strptime(self.get_data_as_dictionary()['active_members'][member], "%Y-%m-%d %H:%M:%S") > datetime.datetime.now() - datetime.timedelta(seconds=30):
                active = True
        if not active:
            self.deactivate()
        return active
    def deactivate(self):
        data = self.get_data_as_dictionary()
        data['active'] = False
        dbs_worker.set_live_focus_mode_data(self.id,data)
        
    
