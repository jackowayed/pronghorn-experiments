#!/usr/bin/python

import subprocess
import time

#from net-test import FlatTopo
from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel
from mininet.cli import CLI

FLOODLIGHT_PATH = "/vagrant/floodlight"
PRONGHORN_PATH = "/vagrant/pronghorn"

class FlatTopo(Topo):
    "N switches, no connections, no hosts"
    def __init__(self, switches=5, **opts):
        Topo.__init__(self, **opts)
        for i in range(switches):
            switch = self.addSwitch("s%s" % (i + 1))

class Experiment:
    def __init__(self, topology, task):
        self.topology = topology
        self.task = task

    def run(self):
        # Run Floodlight
        floodProc = subprocess.Popen(["java", "-jar", FLOODLIGHT_PATH + "/target/floodlight.jar"], stdin=subprocess.PIPE)
        time.sleep(10)
        

        # Run Mininet
        net = Mininet(topo=self.topology, controller=lambda name: RemoteController(name, ip='127.0.0.1'))
        net.start()

        # Run experiment
        out = subprocess.check_output(["ant", "-f", PRONGHORN_PATH + "/src/experiments/pronghorn/build/build.xml", "run_" + self.task])
        print out

        # Teardown
        net.stop()
        floodProc.kill()
        #floodProc.communicate("")
        

#experiments = [Experiment(FlatTopo(switches=1), "NoContentionLatency")]
experiments = [Experiment(FlatTopo(switches=1), "NoContentionThroughput")]#,
               #Experiment(FlatTopo(switches=10), "NoContentionThroughput"),
               #Experiment(FlatTopo(switches=100), "NoContentionThroughput")]

for e in experiments:
    print e.run()
