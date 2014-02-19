#!/usr/bin/env python

import sys
from dist_util import read_conf_file,DEFAULT_JAR_DIRECTORY

def run(local_folder_name):
    host_entry_list = read_conf_file()

    # first remove all existing directories, if they exist
    waiting_procs = []
    ssh_cmd = 'sudo rm -rf %s ' % DEFAULT_JAR_DIRECTORY
    for host_entry in host_entry_list:
        waiting_procs.append(host_entry.issue_ssh(ssh_cmd))

    for proc in waiting_procs:
        proc.wait()
        

    # second copy new one
    waiting_procs = []
    for host_entry in host_entry_list:
        waiting_procs.append(host_entry.scp_to_foreign(
                local_folder_name,DEFAULT_JAR_DIRECTORY,True))

    for proc in waiting_procs:
        proc.wait()


def print_usage():
    print ('''

  ./copy_experiments_dir <local experiments directory>

Copies all files in <local experiments directory> to running host
specified by default cfg file.

''')
        

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print_usage()
    else:
        local_experiments_folder_name = sys.argv[1]
        run(local_experiments_folder_name)

