#!/usr/bin/env python

import subprocess
import sys

HOME = "/home/ubuntu"
EXPERIMENTS_DIR = HOME + "/experiments"
PRONGHORN_DIR = HOME + "/pronghorn"


def git_pull(git_dir):
    p = subprocess.Popen(["git", "fetch"], cwd=git_dir)
    p.wait()
    p = subprocess.Popen(["git", "reset", "--hard", "origin/master"], cwd=git_dir)
    p.wait()
    p = subprocess.Popen(["git", "submodule", "update", "--init", "--recursive"], cwd=git_dir)
    p.wait()
    

def update():
    # Update experiments
    git_pull(EXPERIMENTS_DIR)
    # Update pronghorn
    git_pull(PRONGHORN_DIR)
    





command = sys.argv[1]

if command == "update":
    update()
