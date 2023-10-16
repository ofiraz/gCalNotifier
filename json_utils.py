import json

def nice_json(json_object):
    return(json.dumps(json_object, indent = 1))
