import os
import sys
import re
import commands
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util


def get_operand_string(mean, std_dev):

    """
    Generate the Operand String to be used in workflow nodes to supply 
    mean and std deviation to alff workflow nodes

    Parameters
    ----------

    mean: string
        mean value in string format
    
    std_dev : string
        std deviation value in string format


    Returns
    -------

    op_string : string


    """

    str1 = "-sub %f -div %f" % (float(mean), float(std_dev))

    op_string = str1 + " -mas %s"

    return op_string



def get_opt_string(mask):
    """
    Method to return option string for 3dTstat
    
    Parameters
    ----------
    mask : string (file)
    
    Returns
    -------
    opt_str : string
    
    """
    opt_str = " -stdev -mask %s" %mask
    return opt_str



