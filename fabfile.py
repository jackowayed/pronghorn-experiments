from fab.api import *
from experiment import *
from serialize import *


def experiment(serialized):
    sudo("/home/ubuntu/experiments/manage-host.py experiment " + serialized)
