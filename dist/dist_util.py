#!/usr/bin/env python

import subprocess

DEFAULT_JAR_DIRECTORY = 'experiments_jar'

CONF_FILE_LINES_PER_ENTRY = 4
LISTENING_FOR_CONNECTIONS_ON_PORT = 31521
DEFAULT_CONF_FILE = 'distributed.cfg'
BETWEEN_NODE_WAIT_TIME_SECONDS = 2

def produce_linear_topology_arguments(host_entry_list):
    '''
    @returns {list} --- Each element is a string that contains the
    host-port pairs that the corresponding HostEntry object should try
    to connect to if we were going to create a linear topology

    Note: assumes that last element in host_entry_list is tail
    (connects to no one) and first element is head.

    Example:
       host_entry_list = [a,b,c,d]

       topo: a -> b -> c -> d
    '''
    to_return = []
    for i in range(0,len(host_entry_list) - 1):
        next_entry = host_entry_list[i+1]
        current_entry_args = (
            '%s:%i' % (next_entry.hostname,LISTENING_FOR_CONNECTIONS_ON_PORT))
        to_return.append(current_entry_args)

    if len(host_entry_list) != 0:
        # last controller in line does not try to connect to any other.
        to_return.append('')

    return to_return

def produce_tree_topology_arguments(host_entry_list):
    '''
    @see produce_linear_topology_arguments.

    Example:
       host_entry_list = [a,b,c,d]

       topo:     a
               / | \
              b  c  d
    '''
    to_return = [''] * len(host_entry_list)
    if len(host_entry_list) == 0:
        return to_return
    
    master_host_port_pairs = ''
    for i in range(1,len(host_entry_list)):
        host_entry = host_entry_list[i]
        master_host_port_pairs += (
            '%s:%i,' % (host_entry.hostname,LISTENING_FOR_CONNECTIONS_ON_PORT))
        
    to_return[0] = master_host_port_pairs
    return to_return


def kill_all(host_entry_list,jar_name):
    # tear down all mininets and all experiments
    for host_entry in host_entry_list:
        host_entry.stop_mininet()
        host_entry.issue_pkill(jar_name)


def run_linear_test(jar_name,local_filename,head_num_ops_to_run_per_switch,
                    command_string, max_experiment_wait_time_seconds):
    '''
    @param {String} jar_name --- Does not include name of default jar
    directory.

    @param {String} local_filename --- When experiments are finished
    executing, save the results locally with this filename.

    @param {int} head_num_ops_to_run_per_switch --- The number of
    operations to run from master node.

    @param {String} command_string --- The command to execute from
    within the DEFAULT_JAR_DIRECTORY.  Should be a format string that
    takes in five, ordered parameters:

        1) %s --- The jar to execute
        2) %s --- The who to connect to csv argument
        3) %i --- Which port to listen for connections on
        4) %i --- The number of operations to run
        5) %s --- The name of the file to save results to on foreign host
    
    @param {int} max_experiment_wait_time_seconds --- The time to wait
    for the experiment to finish before tearing everything down and
    copying the result file from head to local machine.
    '''
    foreign_output_filename = 'output.csv'
    host_entry_list = read_conf_file()
    linear_topo_args = produce_linear_topology_arguments(host_entry_list)

    # start sergeant on nodes in reverse order
    for i in range(len(host_entry_list) -1, -1, -1):
        host_entry_to_start = host_entry_list[i]
        who_to_contact_args = linear_topo_args[i]

        if i != 0:
            # non-head node
            num_ops_to_run_per_switch = 0
        else:
            # head            
            num_ops_to_run_per_switch = head_num_ops_to_run_per_switch

        ssh_cmd = 'cd %s; ' % DEFAULT_JAR_DIRECTORY
        ssh_cmd += (command_string %
                    (LATENCY_TEST_JAR_NAME,
                     who_to_contact_args,
                     LISTENING_FOR_CONNECTIONS_ON_PORT,
                     num_ops_to_run_per_switch,
                     foreign_output_filename))

        host_entry_to_start.issue_ssh(ssh_cmd)
        time.sleep(BETWEEN_NODE_WAIT_TIME_SECONDS)

    # now that we've started all nodes, start mininet on all nodes:
    # start in reverse order so that can ensure last node
    for host_entry in reversed(host_entry_list):
        host_entry.start_mininet()

    # wait for experiment to complete
    time.sleep(max_experiment_wait_time_seconds)

    # teardown mininets and experiments
    kill_all(host_entry_list,jar_name)
    
    # collect result file from master
    head = host_entry[0]
    head.collect_result_file(foreign_output_filename,local_filename_to_save_to)


class HostEntry(object):
    def __init__(self,key_filename,username,hostname):
        '''
        @param {string} key_filename --- None if should not use
        keyfile.
        '''
        self.key_filename = key_filename
        self.username = username
        self.hostname = hostname

    def start_mininet(self,num_switches):
        ssh_cmd = 'sudo mn --controller=remote --topo=linear,%i' % num_switches
        self.issue_ssh(ssh_cmd_str)

    def stop_mininet(self):
        self.issue_pkill('mn')
        
    def issue_pkill(self,what_to_pkill):
        cmd_str = 'sudo pkill -f %s' % what_to_pkill
        self.issue_ssh(cmd_str)

    def collect_result_file(self,foreign_filename,local_filename):
        cmd_vec = ['scp','-o','StrictHostKeyChecking=no']
        if self.key_filename is not None:
            cmd_vec.extend(['-i',self.key_filename])
        cmd_vec.append('%s@%s:%s' % (self.username,self.hostname,foreign_filename))
        cmd_vec.append(local_filename)
        p = subprocess.Popen(cmd_vec)
        p.wait()
        
    def issue_ssh(self,ssh_cmd_str,block_until_completion=False):
        cmd_vec = ['ssh','-o','StrictHostKeyChecking=no']
        if self.key_filename is not None:
            cmd_vec.extend(['-i',self.key_filename])
        cmd_vec.append('%s@%s' % (self.username,self.hostname))
        cmd_vec.append(ssh_cmd_str)
        cmd_vec = ['ssh',
                   '-o','StrictHostKeyChecking=no',
                   '%s@%s' % (self.username,self.hostname),
                   ssh_cmd_str]
        p = subprocess.Popen(cmd_vec)
        if block_until_completion:
            p.wait()
        return p
        
    def debug_print(self):
        key_file_txt = 'no key file'
        if self.key_filename is not None:
            key_file_txt = 'key file: %s' % self.key_filename
        
        print '%s@%s; %s' % (self.username,self.hostname,key_file_txt)
        

def read_conf_file(conf_filename=DEFAULT_CONF_FILE):
    '''
    @returns{list} --- each element is a HostEntry object.
    
    Format of conf file should be:

    #entry
    ssh key filename (or "null" if shouldn't use an ssh key)
    username
    hostname
    #entry
    ssh key filename (or "null" if shouldn't use an ssh key)
    username
    hostname
    ...
    
    '''
    with open(conf_filename,'r') as fd:
        conf_contents = fd.read()

    split_conf = conf_contents.split('\n')
    if len(split_conf) % CONF_FILE_LINES_PER_ENTRY != 0:
        print ('Malformed configuration file has incorrrect number of lines')
        assert(False)

    host_entries = []
    for i in range(0,len(split_conf),CONF_FILE_LINES_PER_ENTRY):

        empty = split_conf[i].strip()
        key_filename = split_conf[i+1].strip()
        if key_filename == 'null':
            key_filename = None
        username = split_conf[i+2].strip()
        hostname = split_conf[i+3].strip()
        host_entries.append(HostEntry(key_filename,username,hostname))
    return host_entries
    
    
if __name__ == '__main__':
    host_entry_list = read_conf_file()
    for host_entry in host_entry_list:
        host_entry.debug_print()

    print '\nTree'
    for argument in produce_tree_topology_arguments(host_entry_list):
        print argument
    print '\n'


    print '\nLine'
    for argument in produce_linear_topology_arguments(host_entry_list):
        print argument
    print '\n'
