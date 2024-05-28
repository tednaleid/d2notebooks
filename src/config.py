# load the config file that holds the client_id and api_key used to talk to the Bungie API.
# we are using the "Public" method and only making read-only requests, so we don't need the client_secret
# this also means that our tokens will only be good for 1 hour

import json
import os

def load_config():
    # If config.json is not present, create it with default content
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as file:
            # don't modify this as it'll get checked in, let it create the default file and then you can modify it
            json.dump({ "client_id": "your_client_id", "api_key": "your_api_key", "username": "your_username#1234"}, file, indent=4)

    with open('config.json', 'r') as file:
        data = json.load(file)

    assert 'client_id' in data and 'api_key' in data and 'username' in data, "config.json is missing required fields: client_id, api_key, username" 

    client_id = data['client_id']
    api_key = data['api_key']
    username = data['username']

    assert client_id != '' and client_id != "your_client_id", "Please enter your client_id in the config.json file"
    assert api_key != '' and api_key != "your_api_key", "Please enter your client_id in the config.json file"
    assert username != '' and username != "your_username#1234", "Please enter your username in the config.json file"

    return client_id, api_key, username

