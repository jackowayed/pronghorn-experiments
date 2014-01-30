#!/usr/bin/env python

import subprocess
import time



FLOODLIGHT_REST_PORT = 8080
LISTENING_FOR_PARENT_ON_PORT = 3939
PEM_FILENAME = 'sergeant3.pem'

EXPERIMENT_BUILD_PATH = 'pronghorn/src/experiments/pronghorn/build'


EC2_HOSTS = []

# wait 5 seconds between starting a sergeant instance and its parent.
WAIT_TIME_BETWEEN_SERGEANT_STARTS = 20
# used as a general barrier when one operation depends on another
GENERAL_WAIT_TIME = 30

FAST_WAIT_TIME = 5

# # Example usage
# def run_test_setup():
#     hosts = ['ec2-54-184-51-225.us-west-2.compute.amazonaws.com']
#     # start mininet
#     # start_mininet_and_floodlight(hosts,5)
#     # # run dumb latency test
#     # dumb_latency_test(hosts)
#     # stop mininet and floodlight
#     # stop_mininet_and_floodlight(hosts)
#     collect_data (
#         hosts[0],EXPERIMENT_BUILD_PATH+'/classes/latency_out.csv',
#         'latency_out.csv')

LATENCY_TEST_OUTPUT_FILENAME = 'dist_latency_test2.csv'
LATENCY_NUM_OPS = 1000
DIST_LATENCY_TEST_NAME = 'run_MultiControllerLatency'


DIST_THROUGHPUT_TEST_NAME = 'run_MultiControllerNoContentionThroughput'
THROUGHPUT_NUM_OPS = 1000
NUM_SWITCHES_PER_CONTROLLER = 60
THROUGHPUT_TEST_OUTPUT_FILENAME = (
    'chained_throughput_output_%s_%s.csv' %
    (THROUGHPUT_NUM_OPS, NUM_SWITCHES_PER_CONTROLLER))


def run_test_setup():
    hosts = [
        'ec2-54-202-198-195.us-west-2.compute.amazonaws.com', # node a
        'ec2-54-203-217-172.us-west-2.compute.amazonaws.com', 
        'ec2-54-203-229-215.us-west-2.compute.amazonaws.com',
        'ec2-54-244-102-62.us-west-2.compute.amazonaws.com'
]
    # run_latency_test(hosts,'latency_results.csv')
    # stop_sergeants(hosts,DIST_LATENCY_TEST_NAME)
    
    run_throughput_test(hosts,NUM_SWITCHES_PER_CONTROLLER,'throughput_results.csv')
    
    # stop_mininet_and_floodlight(hosts)
    # stop_sergeants(hosts,DIST_THROUGHPUT_TEST_NAME)
    print '\nWaiting a bit\n'
    time.sleep(FAST_WAIT_TIME)

    
def chmod_all_pronghorn (hosts):
    ssh_cmd_str = 'sudo chmod a=wrx -R pronghorn/'
    for host in hosts:
        issue_ssh(host,ssh_cmd_str)
    

################ THROUGHPUT EXPERIMENT CONSTANTS #############

def run_throughput_test(hosts,switches_per_controller,local_output_file):
    print '\nchmoding all\n'
    # chmod_all_pronghorn (hosts)
    
    # actually bring up mininet and floodlight on each host
    start_mininet_and_floodlight(hosts,switches_per_controller)
    
    arguments = (
        ' -Dthroughput_port_to_listen_for_connections_on=%i ' %
        LISTENING_FOR_PARENT_ON_PORT)
    
    
    # tell head nodes to collect data and collect a particular number
    # of ops.
    head_arguments = ' -Doutput_filename=%s ' % THROUGHPUT_TEST_OUTPUT_FILENAME
    head_arguments += ' -Dthroughput_num_ops=%i ' % THROUGHPUT_NUM_OPS
    head_arguments += arguments

    # tell non-head nodes to do nothing
    non_head_arguments = ' -Dthroughput_num_ops=0 ' 
    non_head_arguments += arguments

    # parents can connect to their children on this ip/port
    point_at_child_arg_name = ' -Dthroughput_children_to_contact_host_ports'

    # start the latency tests in a chained topology
    print '\nCreating chained sergeants\n'
    start_sergeants_chained(
        hosts,DIST_THROUGHPUT_TEST_NAME,head_arguments,non_head_arguments,
        point_at_child_arg_name)
    
    time.sleep(GENERAL_WAIT_TIME*10)

    print '\nCollecting data\n'
    data_filename_on_server = (
        EXPERIMENT_BUILD_PATH + '/classes/' + THROUGHPUT_TEST_OUTPUT_FILENAME)
    collect_data(
        hosts[0],data_filename_on_server, local_output_file)

        

        
############### LATENCY EXPERIMENT CONSTANTS ###############
def run_latency_test(hosts,local_output_file):
    print '\nchmoding all\n'
    chmod_all_pronghorn (hosts)
    
    # actually bring up mininet and floodlight on each host
    start_mininet_and_floodlight(hosts,1)

    arguments = (
        ' -Dlatency_port_to_listen_for_connections_on=%i ' %
        LISTENING_FOR_PARENT_ON_PORT)

    # tell head nodes to collect data and collect a particular number
    # of ops.
    head_arguments = ' -Doutput_filename=%s ' % LATENCY_TEST_OUTPUT_FILENAME
    head_arguments += ' -Dlatency_num_ops=%i ' % LATENCY_NUM_OPS
    head_arguments += arguments

    # tell non-head nodes to do nothing
    non_head_arguments = ' -Dlatency_num_ops=0 ' 
    non_head_arguments += arguments

    # parents can connect to their children on this ip/port
    point_at_child_arg_name = ' -Dlatency_children_to_contact_host_ports'

    # start the latency tests in a chained topology
    print '\nCreating chained sergeants\n'
    start_sergeants_chained(
        hosts,DIST_LATENCY_TEST_NAME,head_arguments,non_head_arguments,
        point_at_child_arg_name)
    
    time.sleep(GENERAL_WAIT_TIME*10)

    print '\nCollecting data\n'
    data_filename_on_server = (
        EXPERIMENT_BUILD_PATH + '/classes/' + LATENCY_TEST_OUTPUT_FILENAME)
    collect_data(
        hosts[0],data_filename_on_server, local_output_file)

    

def dumb_latency_test(hosts):
    '''
    Just run single controller latency test on each host
    '''
    output_filename = 'latency_out.csv'
    ssh_cmd = (
        'cd ' + EXPERIMENT_BUILD_PATH + '; ' + 
        'ant run_SingleControllerLatency -Dlatency_num_ops=100 -Doutput_filename=' +
        output_filename)
    for host in hosts:
        issue_ssh(host,ssh_cmd)

    time.sleep(GENERAL_WAIT_TIME)

        
    

def start_sergeants_chained(
    hosts,test_to_run,head_arguments,non_head_arguments,point_at_child_arg_name):
    '''
    @param {List} hosts --- Each element is a hostname string.  The
    0th entry of the list is the root.  Ie, hosts[0] is the parent for
    hosts[1], hosts[1] is the parent for hosts[2], ...

    @param {List} head_arguments --- The arguments that we should pass
    in to the head node.  Each element is a string.

    @param {List} non_head_arguments --- The arguments that we should
    pass to all non-head nodes.  Each element is a string.
    '''
    # the first entry in hosts is the root
    for reverse_index in reversed(range(0,len(hosts))):
        host = hosts[reverse_index]

        arguments_to_use = non_head_arguments
        if reverse_index == 0:
            arguments_to_use = head_arguments

        if reverse_index != (len(hosts) -1):
            # we are a parent of a child: must explicitly connect to
            # child.
            child_host = hosts[reverse_index + 1]
            arguments_to_use += (
                ' %s=%s:%i' %
                ( point_at_child_arg_name, child_host,LISTENING_FOR_PARENT_ON_PORT))
            
        ant_command = 'ant ' + test_to_run + ' ' + arguments_to_use
        issue_start_sergeant(host,ant_command)
        time.sleep(WAIT_TIME_BETWEEN_SERGEANT_STARTS)

        
def issue_start_sergeant(host_to_start,test_name_and_arguments):
    '''
    @param {String} host_to_start --- Start a sergeant instance on
    this host.
    
    @param {String or None} child_host --- Tell the sergeant instance
    on host host_to_start to connect, as a parent, to running sergeant
    instance on child_host.  If child_host is None, do not connect to
    any child.

    @param {String} additional_arguments --- Each element is a string
    containing an argument we want to pass in when starting the node.
    '''
    issue_ssh(
        host_to_start,
        'cd %s; %s' % (EXPERIMENT_BUILD_PATH, test_name_and_arguments))
    
    
def stop_sergeants(hosts,what_to_pgkill_with):
    '''
    @param {List} hosts --- Each element is a string host name.
    '''
    for host in hosts:
        cmd_str = 'sudo pkill -f %s' % what_to_pgkill_with
        issue_ssh(host,cmd_str)

def start_mininet_and_floodlight(hosts,num_switches):
    # compile floodlight on all hosts
    print '\nCompiling floodlight\n'
    ssh_cmd = 'cd floodlight; ant'
    for host in hosts:
        issue_ssh(host,ssh_cmd)

    time.sleep(5*GENERAL_WAIT_TIME)

    
    # start floodlight on all hosts
    print '\nAbout to start floodlight\n'
    ssh_cmd = 'sudo java -jar floodlight/target/floodlight.jar'
    for host in hosts:
        issue_ssh(host,ssh_cmd)

    time.sleep(GENERAL_WAIT_TIME)
        
    # start mininet on all hosts
    print '\nAbout to start mininet\n'
    ssh_cmd = 'sudo mn --controller=remote --topo=linear,%i' % num_switches
    for host in hosts:
        issue_ssh(host,ssh_cmd)
        
    time.sleep(GENERAL_WAIT_TIME)


def issue_ssh(host,ssh_cmd_str):
    '''
    @param {String} host --- name of host we're ssh-ing to 
    '''
    cmd = ['ssh','-i',PEM_FILENAME,
           '-o','StrictHostKeyChecking=no',
           'ubuntu@%s' % host,ssh_cmd_str]
    subprocess.Popen(cmd)

def collect_data(host_to_collect_from,absolute_data_filename,local_name):
    # TODO
    cmd_vec = [
        'scp','-i',PEM_FILENAME,
        'ubuntu@%s:%s'% (host_to_collect_from, absolute_data_filename),
        local_name]
    p = subprocess.Popen(cmd_vec)
    p.wait()
    
        

def stop_mininet_and_floodlight(hosts):
    for host in hosts:
        # kill mininet
        cmd_str = 'sudo pkill -f mn'
        issue_ssh(host,cmd_str)        
        
        # kill floodlight
        cmd_str = 'sudo pkill -f floodlight'
        issue_ssh(host,cmd_str)


if __name__ == '__main__':
    run_test_setup()
    
