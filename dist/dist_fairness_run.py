#!/usr/bin/env python

import time
import sys
import argparse

from dist_util import read_conf_file, kill_all, run_linear_test
from dist_util import run_tree_test


FAIRNESS_TEST_JAR_NAME = 'multi_controller_fairness.jar'

#DEFAULT_NUM_OPS_TO_RUN = 5000
DEFAULT_NUM_OPS_TO_RUN = 50
# MAX_EXPERIMENT_WAIT_TIME_SECONDS = 450
MAX_EXPERIMENT_WAIT_TIME_SECONDS = 450

def linear_fairness_test(local_filename_to_save_to,
                         num_switches_per_controller,
                         wound_wait,
                         num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):
    wound_wait_string = 'true' if wound_wait else 'false'
    run_linear_test(
        FAIRNESS_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        'java -jar %s %s %i %i false ' + wound_wait_string + ' %s',
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        num_switches_per_controller,
        # last worker should perform writes instead of just reads on
        # switches.
        'java -jar %s %s %i %i true ' + wound_wait_string + ' %s')
    
def tree_fairness_test(local_filename_to_save_to,
                       num_switches_per_controller,
                       wound_wait,
                       num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):

    wound_wait_string = 'true' if wound_wait else 'false'
    run_tree_test(
        FAIRNESS_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        'java -jar %s %s %i %i false ' + wound_wait_string + ' %s',
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        num_switches_per_controller,
        # last worker should perform writes instead of just reads on
        # switches.
        'java -jar %s %s %i %i true ' + wound_wait_string + ' %s')

    
def kill_fairness_experiments(host_entry_list=None):
    if host_entry_list is None:
        host_entry_list = read_conf_file()
    kill_all(host_entry_list,FAIRNESS_TEST_JAR_NAME)


def run_cli():    
    description_string = '''
Use this script to run distributed fairness experiments on ec2 nodes.
'''
    parser = argparse.ArgumentParser(description=description_string)
    parser.add_argument(
        '--kill',action='store_true',
        help='Destroy all running fairness tests and mininets')
    parser.add_argument(
        '--topo',choices=['linear','tree'],
        help='Run the fairness experiment in a linear or tree topology.')
    parser.add_argument(
        '--out',
        help='Name of file to save results to locally.')

    parser.add_argument(
        '--algo',choices=['wound_wait','ralph'],
        help='Which deadlock avoidance algorithm to use.')
    
    parser.add_argument(
        '--num_switches',
        type=int, default=1,
        help='Number of switches to run per controller.')

    
    args = parser.parse_args()
    

    if args.kill:
        kill_fairness_experiments()
    else:
        output_filename = args.out
        if output_filename is None:
            print '\nFairness: if not killing, require output filename.\n'
            return

        topo = args.topo
        if topo is None:
            print '\nFairness: if not killing, require topology.\n'
            return

        algo = args.algo
        if algo is None:
            print '\nFairness: if not killing, require algo.\n'
            return

        wound_wait = False
        if algo == 'wound_wait':
            wound_wait = True
        
        num_switches_per_controller = args.num_switches
        
        if topo == 'linear':
            linear_fairness_test(
                output_filename,num_switches_per_controller,wound_wait)
        elif topo == 'tree':
            tree_fairness_test(
                output_filename,num_switches_per_controller,wound_wait)
        #### DEBUG
        else:
            print ('\nUnexpected topo type\n')
            assert(False)
        #### END DEBUG
    

    
if __name__ == '__main__':
    run_cli()
