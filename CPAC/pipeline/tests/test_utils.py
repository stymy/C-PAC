import os, sys
sys.path.append("/Users/zarrar/Code/C-PAC")

import numpy as np
from numpy.testing import *

from nose.tools import ok_, eq_, raises, with_setup
from nose.plugins.attrib import attr    # http://nose.readthedocs.org/en/latest/plugins/attrib.html

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

def test_gen_file_map():
    """
    So I'm not sure the best way to actually test this.
    For now, this just calls the gen_file_map function and make's sure it 
    returns something reasonable.
    """
    datadir = '/home/data/Projects/CPAC_Regression_Test/2013-08-19-20_v0-3-1/output'
    subject_infos = utils.gen_file_map(datadir, 'path_files/*/*.txt')
    

@attr('configs', 'group')
def test_setup_group_list():
    # So setup_group_subject_list
    # will check conf.subjectListFile
    # and see overlap with subject_infos
    
    config_file     = "files/config_fsl.yml"
    subject_infos   = utils.gen_file_map()
    os.path.join(base_path, 'pipeline_*', '*', 'path_files_here', '*.txt')
    
    curdir = os.getcwd()
    os.chdir(__file__)
    
    conf             = utils.load_configuration(config_file)
    old_subject_file = utils.load_subject_list(conf.subjectListFile)
    new_subject_file = utils.setup_group_subject_list(config_file, subject_infos)
    
    os.chdir(curdir)
    
    # All should be right here
    assert_equal(np.array(old_subject_file), np.array(new_subject_file))
    
    # Case where only one path is correct
    
    
    """
    I want to test a couple of cases:
    - If nothing changes
    - If the subject list actually has subjects with missing data, it detects that
        (here I can actually just modify the subject_infos or actually recall gen_file_map with a list of subject's desired)
    """
    
    
    
    