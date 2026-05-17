from emhub.client import DataClient, open_client
import json

# Connect to the remote server and login using credentials:
dc = DataClient(server_url='https://emhub.hi.umn.edu')
dc.login('admin', 'admin')

# Fetch all users:
users = dc.request('get_users', jsonData=None).json()
#print(users)

# Dump users into a JSON file:
with open('users.json', 'w') as f:
    userList = [{'id': f['id'],
                 'username': f['username'],
                 'email': f['email'],
                 'phone': f['phone'],
                 'name': f['name'],
                 'created': f['created'],
                 'status': f['status'],
                 'roles': f['roles'],
                 'password_hash': f['password_hash'],
                 'profile_image': f['profile_image'],
                 'pi_id': f['pi_id'],
                 'extra': f['extra']
                 }
                for f in users
                ]
    json.dump(userList, f, indent=4)
dc.logout()

# Now connect to another server and load info from JSON file
# Assuming that by default the config are set for the development server:
#with open('users.json') as f:
#    userList = json.load(f)

#with open_client() as dc2:
#    for user in userList:
#        print(f">> Updating user ID={user['id']}\t {user['name']}")
#        dc.request('update_user', jsonData={'attrs': user})
