#!/usr/bin/env python3
import argparse
import os
import subprocess
import nibabel
import numpy
from glob import glob

parser = argparse.ArgumentParser(description='Example BIDS App entrypoint script.')
parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('output_dir', help='The directory where the output files '
                    'should be stored.')
group = parser.add_mutually_exclusive_group()
group.add_argument('--participant_label', help='(optional - first level only) '
                   'label of the participant that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+")
group.add_argument('--first_level_results', help='(group level only) directory with outputs '
                    'from a set of participants which will be used as input to '
                    'the group level (this is where first level pipelines store '
                    'outputs via output_dir).')

args = parser.parse_args()


# running first level
if not args.first_level_results:
    subjects_to_analyze = []
    # only for a subset of subjects
    if args.participant_label:
        subjects_to_analyze = args.participant_label
    # for all subjects
    else:
        subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
        subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

    # find all T1s and skullstrip them
    for subject_label in subjects_to_analyze:
        for T1_file in glob(os.path.join(args.bids_dir, "sub-%s"%subject_label,
                                         "anat", "*_T1w.nii*")):
            out_file = os.path.split(T1_file)[-1].replace("_T1w.", "_brain.")
            cmd = "bet %s %s"%(T1_file, os.path.join(args.output_dir, out_file))
            print(cmd)
            subprocess.run(cmd, shell=True, check=True)

# running group level
else:
    brain_sizes = []
    for brain_file in glob(os.path.join(args.first_level_results, "*.nii*")):
        data = nibabel.load(brain_file).get_data()
        # calcualte average mask size in voxels
        brain_sizes.append((data != 0).sum())

    with open(os.path.join(args.output_dir, "avg_brain_size.txt"), 'w') as fp:
        fp.write("Average brain size is %g voxels"%numpy.array(brain_sizes).mean())
