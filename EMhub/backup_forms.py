#!/usr/bin/python

from emhub.client import DataClient, open_client
import json

# Connect to the server and login
dc = DataClient(server_url='https://emhub.hi.umn.edu')
dc.login('admin', 'admin')

# Fetch all forms
forms = dc.request('get_forms', jsonData=None).json()

# Dump forms into JSON file
with open('forms.json', 'w') as f:
    formList = [{'id': f['id'],
                 'name': f['name'],
                 'definition': f['definition'] 
                 }
                for f in forms 
                ]
    json.dump(formList, f, indent=4)
dc.logout()
