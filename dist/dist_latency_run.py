#!/usr/bin/env python

import time
import sys
import argparse

from dist_util import read_conf_file, kill_all, run_linear_test
from dist_util import run_tree_test


LATENCY_TEST_JAR_NAME = 'multi_controller_latency.jar'

DEFAULT_NUM_OPS_TO_RUN = 10000
MAX_EXPERIMENT_WAIT_TIME_SECONDS = 600

# DEFAULT_NUM_OPS_TO_RUN = 3000
# DEFAULT_NUM_OPS_TO_RUN = 300
# MAX_EXPERIMENT_WAIT_TIME_SECONDS = 45

JAVA_COMMAND_STRING = 'java -jar %s %s %i %i -1 %s no-listener-factory'

def linear_latency_test(local_filename_to_save_to,
                        num_switches_per_controller,
                        num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):
    run_linear_test(
        LATENCY_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        JAVA_COMMAND_STRING,
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        num_switches_per_controller)

def tree_latency_test(local_filename_to_save_to,
                      num_switches_per_controller,
                      num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):
    run_tree_test(
        LATENCY_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        JAVA_COMMAND_STRING,
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        num_switches_per_controller)

    
def kill_latency_experiments(host_entry_list=None):
    if host_entry_list is None:
        host_entry_list = read_conf_file()
    kill_all(host_entry_list,LATENCY_TEST_JAR_NAME)


def run_cli():    
    description_string = '''
Use this script to run distributed latency experiments on ec2 nodes.
'''
    parser = argparse.ArgumentParser(description=description_string)
    parser.add_argument(
        '--kill',action='store_true',
        help='Destroy all running latency tests and mininets')
    parser.add_argument(
        '--topo',choices=['linear','tree'],
        help='Run the latency experiment in a linear or tree topology.')
    parser.add_argument(
        '--out',
        help='Name of file to save results to locally.')

    parser.add_argument(
        '--num_switches',
        type=int, default=1,
        help='Number of switches to run per controller.')

    
    args = parser.parse_args()
    

    if args.kill:
        kill_latency_experiments()
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
        
        if topo == 'linear':
            linear_latency_test(output_filename,num_switches_per_controller)
        elif topo == 'tree':
            tree_latency_test(output_filename,num_switches_per_controller)
        #### DEBUG
        else:
            print ('\nUnexpected topo type\n')
            assert(False)
        #### END DEBUG
    

    
if __name__ == '__main__':
    run_cli()
