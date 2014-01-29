import pickle
import base64

def serialize_experiment(exp):
    return base64.b64encode(pickle.dumps(exp))

def deserialize_experiment(ser):
    return pickle.loads(base64.b64decode(ser))
