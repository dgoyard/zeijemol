##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# to be executed in freesurfer environment (freesurfer_init)

# system import
import os

# caps import
from clindmri.plot.freesurfer_nsaps import freesurfer_snaps_wm

# set your parameters
# - your fsdir
# - the subject for which you want the snaps
# - the axis alogn which you want the snaps to be done
# - the slices interval to capture (from 0 to 255) -> you will generate 3 * 256
# snaps at most (768 files)
# - set the output directory (a subject folder will be created)
fsdir = os.getcwd()
sid = "000000106601"

freesurfer_snaps_wm(fsdir, sid, axis=["C", "A", "S"],
                    slice_interval=[0, 255],
                    output_directory=None)
