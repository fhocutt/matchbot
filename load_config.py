# TODO: Consider encoding
"""
load_config
~~~~~~~~~~~

Load the config file given the path to its containing directory.
"""

import json
import sys
import os

filepath = sys.argv[1]
configfile = os.path.join(filepath, 'config.json')
with open(configfile, 'rb') as configf:
    config = json.loads(configf.read())
