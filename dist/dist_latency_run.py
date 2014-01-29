#!/usr/bin/env python

import subprocess
import time


EC2_HOSTS = []
FLOODLIGHT_REST_PORT = 8080
LISTENING_FOR_PARENT_ON_PORT = 3939
PEM_FILENAME = 'sergeant3.pem'

# wait 5 seconds between starting a sergeant instance and its parent.
WAIT_TIME_BETWEEN_SERGEANT_STARTS = 5 
# used as a general barrier when one operation depends on another
GENERAL_WAIT_TIME = 20

# Example usage
# def run_test_setup():
#     hosts = ['ec2-54-184-51-225.us-west-2.compute.amazonaws.com']
#     start mininet
#     start_mininet_and_floodlight(hosts,5)
#     stop mininet and floodlight
#     stop_mininet_and_floodlight(hosts)

def run_test_setup():
    pass

def start_mininet_and_floodlight(hosts,num_switches):
    # compile floodlight on all hosts
    ssh_cmd = 'cd floodlight; ant'
    for host in hosts:
        issue_ssh(host,ssh_cmd)

    time.sleep(GENERAL_WAIT_TIME)

    
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
    cmd = ['ssh','-i',PEM_FILENAME,'ubuntu@%s' % host,ssh_cmd_str]
    subprocess.Popen(cmd)
    
    

def start_sergeants_chained(hosts,head_arguments,non_head_arguments):
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
        child_host = None
        if reverse_index != (len(hosts) -1):
            child_host = hosts[reverse_index + 1]

        arguments_to_use = non_head_arguments
        if reverse_index == 0:
            arguments_to_use = head_arguments
            
        issue_start_sergeant(host,child_host,arguments_to_use)
        time.sleep(WAIT_TIME_BETWEEN_SERGEANT_STARTS)

        
def issue_start_sergeant(host_to_start,child_host,additional_arguments):
    '''
    @param {String} host_to_start --- Start a sergeant instance on
    this host.
    
    @param {String or None} child_host --- Tell the sergeant instance
    on host host_to_start to connect, as a parent, to running sergeant
    instance on child_host.  If child_host is None, do not connect to
    any child.

    @param {List} additional_arguments --- Each element is a string
    containing an argument we want to pass in when starting the node.
    '''
    # TODO
    
    
def stop_sergeants(hosts):
    '''
    @param {List} hosts --- Each element is a string host name.
    '''
    for host in hosts:
        issue_stop_sergeant(host)


def stop_mininet_and_floodlight(hosts):
    for host in hosts:
        # kill mininet
        cmd_str = 'pkill -f mn'
        issue_ssh(host,cmd_str)        
        
        # kill floodlight
        cmd_str = 'pkill -f floodlight'
        issue_ssh(host,cmd_str)        

        

def collect_data(host_to_collect_from,absolute_data_filename):
    # TODO
    pass
    


if __name__ == '__main__':
    run_test_setup()
    
