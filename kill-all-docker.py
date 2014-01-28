#!/usr/bin/env python

import docker

import subprocess

print "Running docker ps first for you"
subprocess.call(["docker", "ps"])

print ""

s = raw_input("Really kill ALL running containers? [yes/NO] ")
if s != "yes":
    print "doing nothing"
else:
    client = docker.Client(base_url='unix://var/run/docker.sock',
                           version='1.6',
                           timeout=10)

    for c in client.containers():
        print client.kill(c)
    subprocess.call(["docker", "ps"])    
