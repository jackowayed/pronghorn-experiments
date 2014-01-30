#!/usr/bin/env python

import subprocess
import sys
from serialize import *
from experiments import *

EXPERIMENTS_PATH = os.path.join(BASE_PATH, "experiments")

def git_pull(git_dir):
    p = subprocess.Popen(["git", "fetch"], cwd=git_dir)
    p.wait()
    p = subprocess.Popen(["git", "reset", "--hard", "origin/master"], cwd=git_dir)
    p.wait()
    p = subprocess.Popen(["git", "submodule", "update", "--init", "--recursive"], cwd=git_dir)
    p.wait()
    

def update():
    # Update experiments
    git_pull(EXPERIMENTS_PATH)
    # Update pronghorn
    git_pull(PRONGHORN_PATH)

def experiment():
    exp = deserialize_experiment(sys.argv[2])
    exp.run()

def mininet():
    num_switches = int(sys.argv[2])
    net = Mininet(topo=FlatTopo(num_switches), controller=lambda name: RemoteController(name, ip='127.0.0.2'))
    net.start()



command = sys.argv[1]

if command == "update":
    update()
elif command == "experiment":
    experiment()
elif command == "mininet":
    mininet()
else:
    print "doing nothing"
