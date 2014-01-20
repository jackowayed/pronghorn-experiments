#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel
from mininet.cli import CLI



class FlatTopo(Topo):
    "N switches, no connections, no hosts"
    def __init__(self, switches=5, **opts):
        Topo.__init__(self, **opts)
        for i in range(switches):
            switch = self.addSwitch("s%s" % (i + 1))

topo = FlatTopo(switches=5)
net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1'))
net.start()
CLI(net)
net.stop()
