#!/usr/bin/env python

import subprocess

DEFAULT_JAR_DIRECTORY = 'experiments_jar'

CONF_FILE_LINES_PER_ENTRY = 4
LISTENING_FOR_CONNECTIONS_ON_PORT = 31521
DEFAULT_CONF_FILE = 'distributed.cfg'

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
        cmd_str = 'sudo pkill -f %s' % waht_to_pkill
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
        cmd_vec = ['ssh','-i',PEM_FILENAME,
               '-o','StrictHostKeyChecking=no',
               'ubuntu@%s' % host,ssh_cmd_str]
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
