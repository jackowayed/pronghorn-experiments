#!/usr/bin/python

import os
import subprocess
import sys
import time
import threading

#from net-test import FlatTopo
from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel
from mininet.cli import CLI


with open(os.path.dirname(os.path.realpath(__file__)) + "/basedir.txt", 'r') as f:
    BASE_PATH = f.read().strip()
    
EXPERIMENTS_JAR_DIR = os.path.join(BASE_PATH,'experiment_jars')
PAPER_DATA = os.path.join(BASE_PATH, "data")


START = int(time.time())

def reset_start():
    START = int(time.time())

def set_rtt(t_ms):
    """Sets RTT between switches and controller.
    Exception on failure"""

    if (t_ms % 2) != 0:
        print '\nCannot run.  Require even number of rtt when setting rtt\n'
        assert False
    t_ms = t_ms /2

    
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
    path = "%s/%s-%d" % (PAPER_DATA, task, START)
    return path

def output_data_fname(task, basename):
    return "%s/%s.csv" % (data_dir(task), basename)


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


CONTROLLER_OF_PORT = 6633            
class setup():
    def __init__(self, exp):
        self.exp = exp

    def __enter__(self):
        # Run Mininet
        self.net = Mininet(topo=self.exp.topology, build=False, switch=MultiSwitch)
        self.net.addController(
            RemoteController("c0", ip="127.0.0.1", port=CONTROLLER_OF_PORT))
        time.sleep(5)
        self.net.build()
        time.sleep(5)
        self.net.start()
        return self

    def __exit__(self, type, value, traceback):
        set_rtt(0)
        self.net.stop()

            
class Experiment:
    def __init__(
        self, topology, jar_name, output_file,rtt=0,
        arguments=None,
        # default is to not collect statistics
        collect_stats_period_ms = -1,
        num_controllers=1):
        
        self.topology = topology
        self.fq_jar = os.path.join(EXPERIMENTS_JAR_DIR,jar_name)
        self.output_file = output_file
        self.rtt = rtt
        self.num_controllers = num_controllers
        self.arguments = []
        if arguments is not None:
            self.arguments = arguments
        self.arguments.append(str(collect_stats_period_ms))
        self.arguments.append(self.output_file)
        self.arguments = map(
            lambda to_stringify: str(to_stringify),
            self.arguments)
        
    def run(self):
        self.ensure_output_dir()
        set_rtt(self.rtt)
        
        subprocess_thread = threading.Thread(target=self.subproc_thread)
        subprocess_thread.daemon = True
        subprocess_thread.start()
        time.sleep(1)

        with setup(self) as mininet_setup:
            subprocess_thread.join()


    def subproc_thread(self):
        task = ['java','-jar',self.fq_jar]
        task.extend(self.arguments)
        print task
        sys.stdout.flush()
        subprocess.call(task)

    
    def ensure_output_dir(self):
        dirname = os.path.dirname(self.output_file)
        try:
            os.mkdir(dirname)
        except OSError:
            # exists
            None

class ErrorExperiment(Experiment):
    def __init__(self, task_name,num_ops_to_run,
                 non_failure_switches,failure_probability):
        topo = FlatTopo(switches=non_failure_switches)
        jar_name = 'single_controller_error.jar'
        output_file = output_data_fname(
            task_name,
            "%i_switches-%f_failure" % (non_failure_switches,failure_probability))
        arguments = [num_ops_to_run,failure_probability]
        Experiment.__init__(self, topo, jar_name, output_file,0, arguments)

class FairnessExperiment(Experiment):
    def __init__(self, task_name,num_ops_to_run,wound_wait):

        # should be True if using wound/wait for deadlock avoidance.
        # for ralph algo, should be false.
        wound_wait_arg = 'true' if wound_wait else 'false'
        
        topo = FlatTopo(switches=1)
        jar_name = 'single_controller_fairness.jar'
        output_file = output_data_fname(
            task_name,
            "%s" % (wound_wait_arg))
        arguments = [wound_wait_arg,num_ops_to_run]
        Experiment.__init__(self, topo, jar_name, output_file,0, arguments)

        
            
class LatencyExperiment(Experiment):
    def __init__(self, task_name,rtt, num_ops_per_thread, num_threads):
        topo = FlatTopo(switches=1)
        jar_name = 'single_controller_latency.jar'
        output_file = output_data_fname(task_name,"%d-%d" % (rtt * 1000, num_threads))
        arguments = [num_ops_per_thread,num_threads]
        Experiment.__init__(self, topo, jar_name, output_file,rtt, arguments)

class ThroughputExperiment(Experiment):
    def __init__(
        self, num_switches, task_name, coarse_locking_boolean,
        num_threads_per_switch,num_ops_per_thread,filename_num_label=None):
        '''
        @param {String} filename_label --- how experiment should label
        file, if not None.  (If it is None, use num_switches.)
        '''
        if filename_num_label is None:
            filename_num_label = num_switches
        
        topo = FlatTopo(num_switches)
        jar_name = 'single_controller_throughput.jar'
        javaized_coarse_locking = 'true' if coarse_locking_boolean else 'false'

        arguments = [
            str(num_ops_per_thread),javaized_coarse_locking,
            str(num_threads_per_switch)]
        
        # include ms since epoch time in fname.
        # DO NOT create two tests with same task and #switches at same
        # time, because this is timestamp of creation, not execution.
        output_filename = output_data_fname(task_name, "%d"  % filename_num_label)

        Experiment.__init__(
            self,topo,jar_name,output_filename,0,arguments)

class ReadOnlyExperiment(Experiment):
    def __init__(self, task_name,num_ops):
        topo = FlatTopo(1)
        jar_name = 'read_only_latency.jar'

        arguments = [str(num_ops)]
        
        # include ms since epoch time in fname.
        # DO NOT create two tests with same task and #switches at same
        # time, because this is timestamp of creation, not execution.
        output_filename = output_data_fname(task_name,'read_only')

        Experiment.__init__(
            self,topo,jar_name,output_filename,0,arguments)

        
class SpeculationExperiment(Experiment):
    def __init__(self, task_name,should_speculate,rtt,flow_table_entries,
                 num_ops_per_thread):
        '''
        @param {string} task_name --- The name to save the task as.

        @param {bool} should_speculate --- True if backend should
        speculate.  False otherwise.

        @param {int} rtt --- Artificial delay to introduce between
        controller and switch.

        @param {int} flow_table_entries --- The number of flow table
        entries to preload into the switch.

        @param {int} num_ops_per_thread --- The number of operations
        (including warmup) to perform for this experiment.
        '''
        topo = FlatTopo(switches=2)
        jar_name = 'speculation.jar'

        speculation_arg = 'true' if should_speculate else 'false'
        
        output_file = output_data_fname(
            task_name,"%s-%d-%d" % (
                speculation_arg,
                rtt * 1000,
                flow_table_entries))
        arguments = [num_ops_per_thread,speculation_arg,flow_table_entries]
        Experiment.__init__(self, topo, jar_name, output_file,rtt, arguments)

        

DEFAULT_NUM_OPERATIONS_PER_THREAD = 30000
def latency_rtt():
    for rtt in (0,2,4,8):
        LatencyExperiment(
            'single_controller_latency',
            rtt,DEFAULT_NUM_OPERATIONS_PER_THREAD,1).run()

            
def latency_contention():
    for threads in  (1, 2, 4, 6, 8, 10):
        print '\nAbout to run latency_no_rtt threads %i\n' % threads
        LatencyExperiment(
            'single_controller_latency',
            2,DEFAULT_NUM_OPERATIONS_PER_THREAD,threads).run()
            

THROUGHPUT_NO_CONTENTION_NUM_SWITCHES = (1, 5, 10, 20, 60)
def throughput_no_contention():
    for num_switches in THROUGHPUT_NO_CONTENTION_NUM_SWITCHES:
        print (
            '\nRunning no contention throughput test with %i switches\n' %
            num_switches)
        
        ThroughputExperiment(
            num_switches,'NoContentionThroughput',False,
            1,DEFAULT_NUM_OPERATIONS_PER_THREAD).run()
        
def throughput_no_contention_coarse_lock():
    for num_switches in THROUGHPUT_NO_CONTENTION_NUM_SWITCHES:
        ThroughputExperiment(
            num_switches,'CoarseNoContentionThroughput',True,
            1,DEFAULT_NUM_OPERATIONS_PER_THREAD).run()

        
THROUGHPUT_CONTENTION_NUM_THREADS = (1,2,4,8,10)
def throughput_contention():
    for num_threads in THROUGHPUT_CONTENTION_NUM_THREADS:
        ThroughputExperiment(
            1,'ContentionThroughput',False,
            num_threads,DEFAULT_NUM_OPERATIONS_PER_THREAD,
            num_threads).run()
        
def error_experiment():
    ErrorExperiment('ErrorExperiment',1000,10,.01).run()
    ErrorExperiment('ErrorExperiment',1000,10,.05).run()
    ErrorExperiment('ErrorExperiment',1000,10,.1).run()


def fairness_experiment():
    FairnessExperiment('FairnessExperiment',30000,True).run()
    FairnessExperiment('FairnessExperiment',30000,False).run()


def read_only_experiment():
    ReadOnlyExperiment('ReadOnly',30000).run()
    
    
# run speculation and no speculation tests as we vary the rtt between
# switch and controller
def speculation_across_rtts():
    for rtt in (0,2,4,8):
        for should_speculate in (True,False):
            print ('\nRunning speculation experiment with rtt %i.\n' % rtt)
            SpeculationExperiment(
                'speculation_rtt',should_speculate,rtt,0,
                DEFAULT_NUM_OPERATIONS_PER_THREAD).run()
            
# run speculatively and non-speculatively on differently-sized
# ftables.
def speculation_across_ftable_size():
    for ftable_preload in (0,100,500,1000,5000,10000):
        for should_speculate in (True,False):
            print (
                '\nRunning speculation experiment with %i ftable entries preloaded.\n' %
                ftable_preload)
            SpeculationExperiment(
                'speculation_ftable',should_speculate,0,ftable_preload,
                DEFAULT_NUM_OPERATIONS_PER_THREAD).run()

