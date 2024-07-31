import json

config = {}
with open("config.json", "r") as config_file:
    config = json.loads(config_file.read())
    
    