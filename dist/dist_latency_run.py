#!/usr/bin/env python

from dist_util import read_conf_file, kill_all, run_linear_test
import time
import sys

LATENCY_TEST_JAR_NAME = 'multi_controller_latency.jar'

DEFAULT_NUM_OPS_TO_RUN = 1000

MAX_EXPERIMENT_WAIT_TIME_SECONDS = 50

def linear_latency_test(local_filename_to_save_to,
                        num_ops_per_switch=DEFAULT_NUM_OPS_TO_RUN):

    run_linear_test(
        LATENCY_TEST_JAR_NAME,
        local_filename_to_save_to,
        num_ops_per_switch,
        'java -jar %s %s %i %i %s',
        MAX_EXPERIMENT_WAIT_TIME_SECONDS,
        1)

def kill_latency_experiments(host_entry_list=None):
    if host_entry_list is None:
        host_entry_list = read_conf_file()
    kill_all(host_entry_list,LATENCY_TEST_JAR_NAME)


def print_usage():
    print ('''

    ./dist_latency_run <arg>

        <arg> --- Either -kill, to destroy all latency tests and
        partially running latency tests on all hosts or name of file to
        save results to locally.

''')
    
        
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print_usage()
    else:
        if sys.argv[1] == '-kill':
            kill_latency_experiments()
        else:
            linear_latency_test(sys.argv[1])
    
