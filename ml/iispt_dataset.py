# A dataset reads into a directory
# The directory can contain several sets, each has 1 directory
# root_directory
# \-set1
#   \-train.json
#    -d_0_0.pfm
#    -p_0_0.pfm
#    -...
#  -set2
#   \-...
#
# Each set contains a train.json file:
# {normalization_intensity, normalization_distance}
# That give the normalization values
# Optional keys:
# {validation_only} - boolean - declares an entire directory
# to be used only for validation.
#
# Dataset files are named like:
# type_x_y.pfm
# type can be:
# p - path traced ground truth
# d - low quality input
# n - normals
# z - depth
#
# Python dataset representation
# A data item contains keys of the same names:
# {p, d, n, z}
# Each value is a PfmImage object
#
# The dataset contains a list of objects:
# {directory, x, y, log_normalization, sqrt_normalization}
# These files are loaded from disk when requested only

# =============================================================================

import os
import json
import torch
import numpy
import random
from torch.utils.data import Dataset, DataLoader

import pfm
import km
import config

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

# Initialize random fixed seed
random.seed(0)

# =============================================================================
# Constants

TYPE_PREFIXES = ["p", "d", "n", "z"]
GAMMA_VALUE = 1.2

# =============================================================================
# Utilities

# -----------------------------------------------------------------------------
def generate_pfm_filenames(dirname, x, y):
    results = []
    for p in TYPE_PREFIXES:
        a_name = os.path.abspath(os.path.join(dirname, "{}_{}_{}.pfm".format(p, x, y)))
        results.append(a_name)
    return results

# -----------------------------------------------------------------------------
# Takes 3 PfmImage objects and returns a ConvNpArray for network input
# <return> a (7, height, width) shaped nparray
def concatenate_conv_np_arrays(intensity, normals, distance):
    intData = intensity.data
    normData = normals.data
    distData = distance.data
    height, width, _ = intData.shape
    res = numpy.zeros((7, height, width), dtype=numpy.float32)

    for y in range(height):
        for x in range(width):
            # Copy intensity data
            res[0, y, x] = intData[y, x, 0]
            res[1, y, x] = intData[y, x, 1]
            res[2, y, x] = intData[y, x, 2]
            # Copy normals data
            res[3, y, x] = normData[y, x, 0]
            res[4, y, x] = normData[y, x, 1]
            res[5, y, x] = normData[y, x, 2]
            # Copy distance data
            res[6, y, x] = distData[y, x, 0]

    return res

# -----------------------------------------------------------------------------
# Takes a single PfmImage and returns a ConvOutNpArray
def pfm_to_conv_np_array(intensity):
    intData = intensity.data
    height, width, _ = intData.shape
    res = numpy.zeros((3, height, width), dtype=numpy.float32)

    for y in range(height):
        for x in range(width):
            res[0, y, x] = intData[y, x, 0]
            res[1, y, x] = intData[y, x, 1]
            res[2, y, x] = intData[y, x, 2]
    return res


# =============================================================================
class IISPTDataset(Dataset):

    # -------------------------------------------------------------------------
    def __init__(self, data_list):
        # [{directory, x, y, log_normalization, sqrt_normalization, validation}]
        self.data_list = data_list
    
    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self.data_list)
    
    # -------------------------------------------------------------------------
    def get_datum(self, idx):
        if idx < 0 or idx >= len(self.data_list):
            return None
        else:
            return self.data_list[idx]
    
    # -------------------------------------------------------------------------
    # <return> {
    #   p        nparray ground truth flattened and processed
    #   t        nparray net input flattened and processed
    #   p_name   path to p file
    #   d_name   path to d file
    #   n_name   path to n file
    #   z_name   path to z file
    #   mean     mean of D, returned by d_pfm normalize intensity downstream full
    # }
    def __getitem__(self, idx):
        datum = self.data_list[idx]
        dirname = datum["directory"]
        x = datum["x"]
        y = datum["y"]
        log_normalization = datum["log_normalization"]
        sqrt_normalization = datum["sqrt_normalization"]

        # Generate file names
        p_name, d_name, n_name, z_name = generate_pfm_filenames(dirname, x, y)

        # Load PFM files
        p_pfm = pfm.load(p_name)
        d_pfm = pfm.load(d_name)
        n_pfm = pfm.load(n_name)
        z_pfm = pfm.load(z_name)

        # p_pfm.save_pfm("TMP_P_ORIGINAL.pfm")
        # d_pfm.save_pfm("TMP_D_ORIGINAL.pfm")
        # n_pfm.save_pfm("TMP_N_ORIGINAL.pfm")
        # z_pfm.save_pfm("TMP_Z_ORIGINAL.pfm")

        # Transform P
        p_pfm.normalize_intensity_downstream_half()

        # Transform D
        dmean = d_pfm.normalize_intensity_downstream_full()

        # Transform N
        n_pfm.normalize(-1.0, 1.0)

        # Transform Z
        z_pfm.normalize_distance_downstream_full()

        # Convert from numpy to tensors and create results
        result = {}

        result["p"] = torch.from_numpy(pfm_to_conv_np_array(p_pfm)).float()

        result["t"] = torch.from_numpy(concatenate_conv_np_arrays(d_pfm, n_pfm, z_pfm)).float()

        result["p_name"] = p_name

        result["d_name"] = d_name

        result["n_name"] = n_name

        result["z_name"] = z_name

        result["mean"] = dmean

        return result

# =============================================================================
# Dataset loading

# -----------------------------------------------------------------------------
# (private)
# Returns a tuple (t, x, y)
# with example_type, x, y
def parse_filename(fname):
    if not fname.endswith(".pfm"):
        return None
    splt = fname.split(".")
    if len(splt) != 2:
        return None
    fname = splt[0]
    splt = fname.split("_")
    if len(splt) != 3:
        return None
    try:
        t = splt[0]
        if not (t in TYPE_PREFIXES):
            return None
        x = int(splt[1])
        y = int(splt[2])
        if (x < 0) or (y < 0):
            return None
        return (t, x, y)
    except:
        return None

# -----------------------------------------------------------------------------
# (private)
# Check that the related prefixes to the coordinate exist
# Returns None if all ok
# Returns an information message otherwise
def check_siblings_exist(set_dir_path, x, y):
    sb = ""
    problems_found = False
    for prefix in TYPE_PREFIXES:
        fname = "{}_{}_{}.pfm".format(prefix, x, y)
        fpath = os.path.abspath(os.path.join(set_dir_path, fname))
        if not os.path.isfile(fpath):
            sb += "[{}] not found.\n".format(fpath)
            problems_found = True
    if problems_found:
        return sb
    else:
        return None

# -----------------------------------------------------------------------------
# (private)
def load_set_directory(set_dir_name, set_dir_path, results_dict, validation_probability):
    # Info
    print("Loading set directory {}".format(set_dir_path))

    # Read train.json file
    json_file_path = os.path.abspath(os.path.join(set_dir_path, "train.json"))
    if not os.path.isfile(json_file_path):
        print("No train.json found")
        return
    json_file = open(json_file_path, "r")
    train_info = json.load(json_file)
    json_file.close()
    normalization_intensity = train_info["normalization_intensity"]
    normalization_distance = train_info["normalization_distance"]
    validation_only = False
    if "validation_only" in train_info:
        validation_only = train_info["validation_only"]

    # Iterate through all the files
    set_content = os.listdir(set_dir_path)
    added_current = 0
    for a_file_name in set_content:
        # Parse X and Y from filename
        filename_data = parse_filename(a_file_name)
        if filename_data is None:
            # This file isn't relevant for the training
            continue
        t, x, y = filename_data

        # Check if this data item is already in the train set
        k = "{}_{}_{}".format(set_dir_name, x, y)
        if k in results_dict:
            # This example is already in
            continue
        
        # Check if related siblings exist
        check_message = check_siblings_exist(set_dir_path, x, y)
        if check_message is not None:
            print("WARNING: training example {} {} {} incomplete: {}".format(set_dir_name, x, y, check_message))
        
        # Add to results
        value = {}
        value["directory"] = set_dir_path
        value["x"] = x
        value["y"] = y
        value["log_normalization"] = normalization_intensity
        value["sqrt_normalization"] = normalization_distance
        # validation key
        if validation_only:
            value["validation"] = True
        elif random.random() < validation_probability:
            value["validation"] = True
        else:
            value["validation"] = False
        results_dict[k] = value
        added_current += 1
    
    print("Added {} examples in {}".format(added_current, set_dir_path))

# -----------------------------------------------------------------------------
# Returns a tuple (training_dataset, validation_dataset)
# Each dataset is a Pytorch Dataset
def load_dataset(root_directory, validation_probability):
    # Key: setname_x_y
    # Value: {directory, x, y, log_normalization, sqrt_normalization, validation}
    results_dict = {}

    # List directory contents
    root_content = os.listdir(root_directory)

    # Explore each directory
    for set_dir in root_content:
        set_dir_abs = os.path.abspath(os.path.join(root_directory, set_dir))
        load_set_directory(set_dir, set_dir_abs, results_dict, validation_probability)
    
    # Create the list of results
    results_train = []
    results_validation = []
    for k in results_dict:
        v = results_dict[k]
        if v["validation"]:
            results_validation.append(v)
        else:
            results_train.append(v)
    
    # Create Dataset object
    r_t, r_v = (IISPTDataset(results_train), IISPTDataset(results_validation))
    print("Loaded {} training, {} validation examples".format(r_t.__len__(), r_v.__len__()))
    return (r_t, r_v)

# =============================================================================

def main_test():
    dt, dv = load_dataset(config.dataset, 0.1)
    print("Loaded {} + {} examples".format(dt.__len__(), dv.__len__()))
    print(dv.__getitem__(0))

# main_test()