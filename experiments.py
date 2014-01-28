#!/usr/bin/python

import os
import subprocess
import sys
import time


import docker

#from net-test import FlatTopo
from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel
from mininet.cli import CLI

FLOODLIGHT_PATH = "/vagrant/floodlight"
PRONGHORN_PATH = "/vagrant/pronghorn"
PRONGHORN_BUILD_DIR = PRONGHORN_PATH + "/src/experiments/pronghorn/build"
PAPER_DATA = "/vagrant/sigcomm2014-pronghorn-data/data"

OPENFLOW_PORT=6633
REST_PORT=8080

DOCKER = docker.Client(base_url='unix://var/run/docker.sock',
                       version='1.6',
                       timeout=10)

START = int(time.time())

def set_rtt(t_ms):
    """Sets RTT between switches and controller.
    Exception on failure"""
    subprocess.call(["tc", "qdisc", "add", "dev", "lo", "root",
                     "handle", "1:", "prio"])
    # Delete rule in case it's there, ignore failure in case it's not
    subprocess.call(["tc", "qdisc", "del", "dev", "lo", "parent", "1:3",
                     "handle", "10:", "netem", "delay", "%dms" % t_ms])
    status = subprocess.check_call(["tc", "qdisc", "add", "dev", "lo", "parent", "1:3",
                              "handle", "10:", "netem", "delay", "%dms" % t_ms])
    subprocess.check_call(["tc", "filter", "add", "dev", "lo", "protocol",
                           "ip", "parent", "1:0", "prio", "3", "u32", "match",
                           "ip", "dst", "127.0.0.2/32", "flowid", "1:3"])



def data_dir(task):
    path = "%s/%s-%d/" % (PAPER_DATA, task, START)
    try:
        os.mkdir(path)
    except OSError:
        # exists
        None
    return path

def data_fname_flag(task, basename):
    return "-Doutput_filename=%s/%s.csv" % (data_dir(task), basename)


class MultiSwitch( OVSSwitch ):
    "Custom Switch() subclass that connects to different controllers"
    def start( self, controllers ):
        my_num = int(self.name[1:])-1
        return OVSSwitch.start( self, [ controllers[my_num % len(controllers)] ] )

class FlatTopo(Topo):
    "N switches, no connections, no hosts"
    def __init__(self, switches=5, **opts):
        Topo.__init__(self, **opts)
        for i in range(switches):
            switch = self.addSwitch("s%d" % (i + 1))

IMAGE = "jackowayed/floodlight"
class FloodlightContainer:
    def __init__(self, docker_client):
        self.client = docker_client
        self.did = self.client.create_container(IMAGE, ports=[OPENFLOW_PORT, REST_PORT])["Id"]
        self.client.start(self.did, port_bindings={OPENFLOW_PORT: None,
                                                   REST_PORT: None})
        containers = [c for c in self.client.containers() if c["Id"] == self.did]
        if len(containers) != 1:
            print containers
            print len(containers)
            assert(False)
        c = containers[0]
        for port in c["Ports"]:
            if port["PrivatePort"] == OPENFLOW_PORT:
                self.of_port = port["PublicPort"]
            if port["PrivatePort"] == REST_PORT:
                self.rest_port = port["PublicPort"]

    def kill(self):
        self.client.kill(self.did)


class setup():
    def __init__(self, exp):
        self.exp = exp

    def __enter__(self):
        set_rtt(self.exp.rtt)
        self.containers = []
        # Run Mininet
        self.net = Mininet(topo=self.exp.topology, build=False, switch=MultiSwitch)

        # Run floodlights
        for i in range(self.exp.num_controllers):
            c = FloodlightContainer(DOCKER)
            self.containers.append(c)
            self.net.addController(RemoteController("c%d" % i, ip="127.0.0.2", port=c.of_port))
        time.sleep(5)
        self.net.build()
        time.sleep(5)
        self.net.start()
        return self


    def __exit__(self, type, value, traceback):
        set_rtt(0)
        self.net.stop()
        for c in self.containers:
            c.kill()


class Experiment:
    def __init__(self, topology, task, rtt=0, ant_extras=(), num_controllers=1):
        self.topology = topology
        self.task = task
        self.rtt = rtt
        self.ant_extras=ant_extras
        self.num_controllers = num_controllers

    def run(self):
        with setup(self) as s:
            task = ["ant", "-f", PRONGHORN_BUILD_DIR + "/build.xml", "run_" + self.task]
            task.append("-Drest_ports=" + ",".join([ str(c.rest_port) for c in s.containers]))
            task.extend(self.ant_extras)
            print task
            sys.stdout.flush()
            return subprocess.call(task)

class LatencyExperiment(Experiment):
    def __init__(self, rtt, threads=1):
        topo = FlatTopo(switches=1)
        task = "SingleControllerLatency"
        filename_flag = data_fname_flag(task, "%d-%d" % (rtt * 1000, threads))
        flags = [filename_flag]
        flags.append("-Dlatency_num_threads=%d" % threads)
        Experiment.__init__(self, topo, task, rtt, )


class ThroughputExperiment(Experiment):
    def __init__(self, switches, task="NoContentionThroughput", num_controllers=1):
        # include ms since epoch time in fname.
        # DO NOT create two tests with same task and #switches at same time, because this is timestamp of
        # creation, not execution.
        filename_flag = data_fname_flag(task, "%d-%d"  % (switches, int(time.time() * 1000)))
        Experiment.__init__(self, FlatTopo(switches), task, 0, [filename_flag], num_controllers=num_controllers)

class FairnessExperiment(Experiment):
    def __init__(self, wound_wait=False):
        task = "Fairness"
        flags = ["-Dwound_wait=" + str(wound_wait).lower(),
                 data_fname_flag(task, str(wound_wait).lower())]
        Experiment.__init__(self, FlatTopo(2), task, 0,
                            ant_extras=flags, num_controllers=2)

class ErrorExperiment(Experiment):
    def __init__(self, switches, error_percent):
        task = "Error"
        flags = ["-Derror_num_ops_to_run_per_experiment=100",
                 "-Derror_failure_prob=%f" % (float(error_percent)/100),
                 data_fname_flag(task, "%d-%d" % (error_percent, switches))]
        Experiment.__init__(self, FlatTopo(switches), task, 0, ant_extras=flags)



def latency():
    for rtt in (0,2):
        for threads in  (1, 2, 10, 50):
            LatencyExperiment(rtt, threads).run()

def fairness():
    for wound_wait in (True, False):
        print FairnessExperiment(wound_wait).run()

def error():
    for err in (10, 50, 90):
        for switches in (1, 2, 4, 16):
            ErrorExperiment(switches, err).run()


THROUGHPUT_INPUTS = (1,5, 10, 20, 60)
def all_throughput():
    for i in THROUGHPUT_INPUTS:
        for task in ("NoContentionThroughput", "ContentionThroughput",
                     "NoContentionCoarseLockingThroughput",
                     "ContentionCoarseLockingThroughput"):
            print ThroughputExperiment(i, task).run()


#latency()
#fairness()
#for i in range(4):
#    all_throughput()
#error()
#all_throughput()
#ErrorExperiment(50, 16).run()
