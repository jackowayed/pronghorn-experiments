#!/usr/bin/env python

CONF_FILE_LINES_PER_ENTRY = 4
DEFAULT_CONF_FILE = 'distributed.cfg'


class HostEntry(object):
    def __init__(self,key_filename,username,hostname):
        '''
        @param {string} key_filename --- None if should not use
        keyfile.
        '''
        self.key_filename = key_filename
        self.username = username
        self.hostname = hostname
        
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
