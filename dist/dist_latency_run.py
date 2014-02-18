#!/usr/bin/env python

from dist_util import produce_linear_topology_arguments, DEFAULT_JAR_DIRECTORY
from dist_util import produce_tree_topology_arguments, read_conf_file
from dist_util import LISTENING_FOR_CONNECTIONS_ON_PORT
import time

LATENCY_TEST_JAR_NAME = 'multi_controller_latency.jar'

DEFAULT_NUM_OPS_TO_RUN = 1000

BETWEEN_NODE_WAIT_TIME_SECONDS = 2
MAX_EXPERIMENT_WAIT_TIME_SECONDS = 50

def linear_latency_test(local_filename_to_save_to,
                        num_ops_to_run=DEFAULT_NUM_OPS_TO_RUN):
    
    output_filename = 'linear_latency_out.csv'
    host_entry_list = read_conf_file()
    linear_topo_args = produce_linear_topology_arguments(host_entry_list)

    # start sergeant on nodes in reverse order
    for i in range(len(host_entry_list) -1, -1, -1):
        host_entry_to_start = host_entry_list[i]
        who_to_contact_args = linear_topo_args[i]

        if i != 0:
            # non-head node
            num_ops_to_run_per_experiment = 0
        else:
            # head            
            num_ops_to_run_per_experiment = DEFAULT_NUM_OPS_TO_RUN

        ssh_cmd = 'cd %s; ' % DEFAULT_JAR_DIRECTORY
        ssh_cmd += (
            'java -jar %s %s %i %i %s' %
            (LATENCY_TEST_JAR_NAME,who_to_contact_args,
             LISTENING_FOR_CONNECTIONS_ON_PORT,DEFAULT_NUM_OPS_TO_RUN,
             output_filename))

        host_entry_to_start.issue_ssh(ssh_cmd)
        time.sleep(BETWEEN_NODE_WAIT_TIME_SECONDS)

    # now that we've started all nodes, start mininet on all nodes:
    # start in reverse order so that can ensure last node
    for host_entry in reversed(host_entry_list):
        host_entry.start_mininet()


    # wait for experiment to complete
    time.sleep(MAX_EXPERIMENT_WAIT_TIME_SECONDS)

    # tear down all mininets and all experiments
    for host_entry in host_entry_list:
        host_entry.stop_mininet()
        host_entry.issue_pkill(LATENCY_TEST_JAR_NAME)

    # collect result file from master
    head = host_entry[0]
    head.collect_result_file(output_filename,local_filename_to_save_to)
        
        
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print 'Requires name to save output file to'
    else:
        linear_latency_tests(sys.argv[1])
    
