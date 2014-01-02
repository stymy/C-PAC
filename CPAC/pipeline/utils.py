import os
from CPAC.utils import Configuration

def load_configuration(config_file):
    """
    Load the yaml file as a Configuration class.
    """
    try:
    	yaml_content = yaml.load(open(os.path.realpath(config_file), 'r'))
    	return Configuration(yaml_content)
    except:
        raise Exception("Error in reading %s configuration file" % config_file)

def load_subject_list(subject_list_file):
    """
    Load list of subjects from a file
    """
    with open(subject_list_file, 'r') as f:
        sublist_items   = f.readlines()
        subject_list    = [ line.rstrip('\n') for line in sublist_items \
                                if not (line == '\n') and not line.startswith('#') ]
    return subject_list

def load_paths_from_subject_list(subject_list, subject_infos):
    """
    Load paths to data based on subject list and info/paths for all possible subjects
    """
    p_id, s_ids, scan_ids, s_paths  = (list(tup) for tup in zip(*subject_infos))
    ordered_paths = []
    for sub in subject_list:
        for path in s_paths:
            if sub in path:
                ordered_paths.append(path)
    return ordered_paths


###
# For cpac_group_analysis_pipeline.py
###

def setup_group_subject_list(config_file, subject_infos):
    """
    Simple function that filters the list of subjects based on if the input paths exist.
    
    Parameters
    ----------
    config_file : str
        Path to model settings in yaml format
    subject_infos : dict
        Mapping of output types (e.g., functional_mni) to information on each subject's associated output.
        Information on each subject's output is a list of length 4 and this includes pipeline_id, subject_id, 
        scan_id, and subject_path.
    
    Returns
    -------
    model_files_directory : str
        Path to directory with all the model files (e.g., mat, grp, con)
    subject_list_file : str
        Path to file with list of subjects
    """
    
    # Setup
    conf                            = load_configuration(config_file)
    p_id, s_ids, scan_ids, s_paths  = (list(tup) for tup in zip(*subject_infos))
    
    # Load list of subjects
    subject_list = load_subject_list(conf.subjectListFile)
    
    # List of subject paths which do exist
    exist_paths = []
    for sub in subject_list:    # Loop through desired subjects
        for path in s_paths:    # Loop through all subject paths
            if sub in path:     # Is this path of one of the subjects?
                exist_paths.append(sub)
    
    # Check to see if any derivatives of subjects are missing
    # This doesn't do anything except print some information
    if len(list(set(subject_list) - set(exist_paths))) >0:
        print "-------------------------------------------"
        print "List of outputs missing for subjects:"
        print list(set(subject_list) - set(exist_paths))
        print "\n"
        print "..for derivatives:"
        print resource
        print "\n"
        print "..at paths:"
        print os.path.dirname(s_paths[0]).replace(s_ids[0], '*')
        print "-------------------------------------------"
        print '\n'
    
    # Directory for all the model files
    mod_path = os.path.join(os.path.dirname(s_paths[0]).replace(s_ids[0], 'group_analysis_results/_grp_model_%s'%(conf.modelName)), 
                            'model_files')
    
    # Create directory and all sub-directories if needed
    try:
        os.makedirs(mod_path)
        print "Creating directory: %s" % mod_path
    except:
        print "Attempted to create directory, but path already exists:"
        print mod_path
        print '\n'
    
    # Create a new subject path list within the model files output directory
    try:
        new_sub_file    = os.path.join(mod_path, os.path.basename(conf.subjectListFile))
        f               = open(new_sub_file, 'w')
        for sub in exist_paths:
            print >>f, sub
        f.close()
    except:
        print "Error: Could not open subject list file: %s\n" % new_sub_file
        raise Exception
    
    return new_sub_file


def create_models_for_cwas(conf):
    """
    This runs create_fsl_model and then parses the outputs to remove the header information.
    """
    from glob import glob
    
    # Run 'create_fsl_model' script to extract phenotypic data from
    # the phenotypic file for each of the subjects in the subject list
    try:
        from CPAC.utils import create_fsl_model
        create_fsl_model.run(conf, True)
    except Exception, e:
        print "FSL Group Analysis model not successfully created - error in create_fsl_model script"
        raise
    
    # Paths to the mat, grp, and con outputs
    mat_file = glob(os.path.join(conf.outputModelFilesDirectory, "*.mat"))[0]
    con_file = glob(os.path.join(conf.outputModelFilesDirectory, "*.con"))[0]
    grp_file = glob(os.path.join(conf.outputModelFilesDirectory, "*.grp"))[0]
    
    
    ## Regressors
    
    # Read mat file without FSL header information
    # containing regressors
    mat = np.loadtxt(mat_file, skiprows=5)
    
    
    ## Contrasts
    
    # Read in con file. Can only have one contrast or F-test
    # First get number of lines to skip
    with open(con_file, 'r') as f:
        line_skip = [ i+1 for i,l in enumerate(f.readlines()) if l.strip() == "/Matrix" ][0]
    con = np.loadtxt(con_file, skiprows=line_skip)
    
    # Ensure that only one contrast exists and has 0s and 1s
    if con.shape[0] != 1:
        raise Exception("You can only have one contrast for CWAS. For multiple contrasts, create a new config file.")
    for i in set(con[0,:]):
        if i not in [0,1]:
            raise Exception("You can only have 0's and 1's in contrasts for CWAS.")
    
    # Convert into a list of column indices
    cols = con[0,:].nonzero()
    
    
    ## Strata
    
    # Read in the permutation stratafication file
    strata = np.loadtxt(grp_file, skiprows=4)
    
    # Set to None if all values are the same
    # Otherwise to a list
    if np.all(strata == strata[0]):
        strata = None
    else:
        strata = strata.tolist()
        
        
    return (mat, cols, strata)


###
# For cpac_group_runner.py
###

def gen_file_map(base_path, resource_paths=None):
    """
    Generate the mapping of different resources (e.g., functional_mni or sca) 
    to the file paths of those resources across subjects/scans.
    
    Parameters
    ----------
    base_path : string
        Path to CPAC output directory containing preprocessed data for individual subjects
    resource_paths : None or string or list (default = None)
        Path to file(s) in each subject's CPAC directory containing path information.
        Can include glob-style * or ? that will be expanded and can be a string or list.
        If this is None, then it will autoset to `os.path.join(base_path, 'pipeline_*', '*', 'path_files_here', '*.txt')`.
    
    Returns
    -------
    subject_infos : dict
        Mapping of output types (e.g., functional_mni) to information on each subject's associated output.
        Information on each subject's output is a list of length 4 and this includes pipeline_id, subject_id, 
        scan_id, and subject_path.
    """
    import os
    from glob import glob
    from CPAC.pipeline.cpac_group_runner import split_folders
    
    if resource_paths is None:
        resource_paths = os.path.join(base_path, 'pipeline_*', '*', 'path_files_here', '*.txt')
    
    if isinstance(resource_paths, str):
        resource_paths = [resource_paths]
    
    # Look through resource paths and expand
    # Then read in file paths
    subject_paths = []
    for resource_path in resource_paths:
        files = glob(os.path.abspath(resource_path))
        for file in files:
            path_list = open(file, 'r').readlines()
            subject_paths.extend([s.rstrip('\r\n') for s in path_list])
    
    if len(subject_paths) == 0:
        raise Exception("No subject paths found based on given resource_paths")
    
    # Remove any duplicate paths
    set_subject_paths   = set(subject_paths)
    subject_paths       = list(set_subject_paths)
    
    # Setup an mapping between resource and path info
    # so a dictionary with a list as the default value
    from collections import defaultdict
    analysis_map    = defaultdict(list)
    
    # Parse each subject path into 4 relevant parts: 
    # pipeline_id, subject_id, scan_id, and subject_path
    for subject_path in subject_paths:
        # Removes the base path
        rs_path     = subject_path.replace(base_path, "", 1)
        rs_path     = rs_path.lstrip('/')
        
        # Split the path into a list (of folders)
        folders     = split_folders(rs_path)
        
        # If there aren't at least 4 sub-folders, then something is amiss
        if len(folders) < 4:
            raise Exception("Incorrect subject path, only %i sub-folders found: %s" % (len(folders), subject_path))
        
        # Extract the desired elements
        pipeline_id = folders[0]
        subject_id  = folders[1]
        resource_id = folders[2]    # e.g., functional_mni, falff, etc
        scan_id     = folders[3]
        
        # Add to the mappings (seperate one for group analysis)
        # Note that the key is actually a tuple of the resource_id and key
        key         = subject_path.replace(subject_id, '*')
        analysis_map[(resource_id, key)].append((pipeline_id, subject_id, scan_id, subject_path))
    
    return analysis_map

