#!/usr/bin/python

import subprocess
import time

import data

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



class FlatTopo(Topo):
    "N switches, no connections, no hosts"
    def __init__(self, switches=5, **opts):
        Topo.__init__(self, **opts)
        for i in range(switches):
            switch = self.addSwitch("s%d" % (i + 1))


class setup():
    def __init__(self, exp):
        self.exp = exp

    def __enter__(self):
        set_rtt(self.exp.rtt)
        # Run Floodlight
        self.floodProc = subprocess.Popen(["java", "-jar", FLOODLIGHT_PATH + "/target/floodlight.jar"], stdin=subprocess.PIPE)
        time.sleep(10)
        # Run Mininet
        self.net = Mininet(topo=self.exp.topology, controller=lambda name: RemoteController(name, ip='127.0.0.2'))
        self.net.start()


    def __exit__(self, type, value, traceback):
        set_rtt(0)
        self.net.stop()
        self.floodProc.kill()
        
    


class Experiment:
    def __init__(self, topology, task, rtt=0, ant_extras=()):
        self.topology = topology
        self.task = task
        self.rtt = rtt
        self.ant_extras=ant_extras

    def run(self):
        with setup(self):
            task = ["ant", "-f", PRONGHORN_BUILD_DIR + "/build.xml", "run_" + self.task]
            task.extend(self.ant_extras)
            print task
            return subprocess.check_output(task)

class LatencyExperiment(Experiment):
    def __init__(self, rtt, threads=1):
        topo = FlatTopo(switches=1)
        filename_flag = "-Doutput_filename=%s/latency_no_contention/%d-%d.csv" % (PAPER_DATA, rtt * 1000, threads)
        flags = [filename_flag]
        flags.append("-Dlatency_num_threads=%d" % threads)
        Experiment.__init__(self, topo, "SingleControllerLatency", rtt, )


class ThroughputExperiment(Experiment):
    def __init__(self, switches, task="NoContentionThroughput"):
        # include ms since epoch time in fname.
        # DO NOT create two tests with same task and #switches at same time, because this is timestamp of
        # creation, not execution.
        filename_flag = "-Doutput_filename=%s/%s/%d-%d.csv" % (PAPER_DATA, task, switches, int(time.time() * 1000))
        Experiment.__init__(self, FlatTopo(switches), task, 0, [filename_flag])



def latency():
    for rtt in (0,2):
        for threads in  (1, 2, 10, 50):
            LatencyExperiment(rtt, threads).run()


THROUGHPUT_INPUTS = (1,5, 10, 20, 50)
def all_throughput():
    for i in THROUGHPUT_INPUTS:
        for task in ("NoContentionThroughput", "ContentionThroughput",
                     "NoContentionCoarseLockingThroughput",
                     "ContentionCoarseLockingThroughput"):
            print ThroughputExperiment(i, task).run()

latency()
for i in range(5):
    all_throughput()
