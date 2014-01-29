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
    exp.ensure_output_dir()
    exp.run()




command = sys.argv[1]

if command == "update":
    update()
if command == "experiment":
    experiment()
