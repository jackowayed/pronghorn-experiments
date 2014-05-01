#!/usr/bin/env python

import time
import sys
import argparse

from dist_util import read_conf_file, kill_all, run_linear_test
from dist_util import run_tree_test


SPECULATION_TEST_JAR_NAME = 'multi_controller_speculation_throughput.jar'

DEFAULT_NUM_OPS_TO_RUN = 10000
MAX_EXPERIMENT_WAIT_TIME_SECONDS = 3000

# DEFAULT_NUM_OPS_TO_RUN = 3000
# DEFAULT_NUM_OPS_TO_RUN = 300
# MAX_EXPERIMENT_WAIT_TIME_SECONDS = 45


def linear_speculation_test(local_filename_to_save_to,
                            num_switches_per_controller,
                            should_speculate_arg,
                            num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):
    
    run_linear_test(
        SPECULATION_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        'java -jar %s %s %i %i ' + should_speculate_arg + ' -1 %s',
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        num_switches_per_controller)

def tree_speculation_test(local_filename_to_save_to,
                          num_switches_per_controller,
                          should_speculate_arg,
                          num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):
    run_tree_test(
        SPECULATION_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        'java -jar %s %s %i %i ' + should_speculate_arg + ' -1 %s',
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        num_switches_per_controller)

    
def kill_speculation_experiments(host_entry_list=None):
    if host_entry_list is None:
        host_entry_list = read_conf_file()
    kill_all(host_entry_list,SPECULATION_TEST_JAR_NAME)


def run_cli():    
    description_string = '''
Use this script to run distributed speculation experiments on ec2 nodes.
'''
    parser = argparse.ArgumentParser(description=description_string)
    parser.add_argument(
        '--kill',action='store_true',
        help='Destroy all running speculation tests and mininets')
    parser.add_argument(
        '--topo',choices=['linear','tree'],
        help='Run the speculation experiment in a linear or tree topology.')
    parser.add_argument(
        '--should_speculate',choices=['true','false'],
        help='Speculate or do not speculate when running.')
    parser.add_argument(
        '--out',
        help='Name of file to save results to locally.')

    parser.add_argument(
        '--num_switches',
        type=int, default=1,
        help='Number of switches to run per controller.')

    
    args = parser.parse_args()
    

    if args.kill:
        kill_speculation_experiments()
    else:
        output_filename = args.out
        if output_filename is None:
            print '\nError: if not killing, require output filename.\n'
            return

        topo = args.topo
        if topo is None:
            print '\nError: if not killing, require topology.\n'
            return

        num_switches_per_controller = args.num_switches

        should_speculate = args.should_speculate
        if should_speculate is None:
            print '\nError: if not killing, require should_speculate.\n'
            return
        
        if topo == 'linear':
            linear_speculation_test(
                output_filename,num_switches_per_controller,should_speculate)
        elif topo == 'tree':
            tree_speculation_test(
                output_filename,num_switches_per_controller,should_speculate)
            
        #### DEBUG
        else:
            print ('\nUnexpected topo type\n')
            assert(False)
        #### END DEBUG
    

    
if __name__ == '__main__':
    run_cli()
