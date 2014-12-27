import json
import sys
import os

filepath = sys.argv[1]
configfile = os.path.join(filepath, 'config.json')
with open(configfile, 'rb') as configf:
    config = json.loads(configf.read())
