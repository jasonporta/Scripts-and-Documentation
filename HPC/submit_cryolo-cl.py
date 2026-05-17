#!/usr/bin/python

import optparse
import os
import subprocess
import sys
import time


# =========================
def setupParserOptions():
    parser = optparse.OptionParser()
    parser.set_usage("%prog --dir=<folder with mrc frames> --diam=<diameter in pixels>\n")
    parser.add_option("--dir", dest="dir", type="string", metavar="DIRECTORY",
                      help="Specify directory with .mrc micrographs for picking with cryolo")
    parser.add_option("--diam", dest="diam", type="int", metavar="DIAMETER",
                      help="Specify diameter of particle (in pixels)")
    parser.add_option("--thresh", dest="thresh", type="float", metavar="THRESHOLD", default=0.2,
                      help="Specify threshold for picking (Default=0.2, usually works!)")
    parser.add_option("--negstain", action="store_true", dest="stain", default=False,
                      help="Specify this flag for negative stain micrographs")
    parser.add_option("-d", action="store_true", dest="debug", default=False,
                      help="debug")

    options, args = parser.parse_args()

    if len(args) > 0:
        parser.error("Unknown commandline options: " + str(args))
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit()
    params = {}
    for i in parser.option_list:
        if isinstance(i.dest, str):
            params[i.dest] = getattr(options, i.dest)
    return params


# ==============================
if __name__ == "__main__":

    params = setupParserOptions()

    if not os.path.exists(params['dir']):
        print('Error: Input directory does not exist %s' % (params['dir']))
        sys.exit()

    config_file_path = os.path.join(params['dir'], 'config.json')
    batch_script_path = os.path.join(params['dir'], 'submit_cryolo.sh')
    # Write config script
    if params['stain'] is False:
        o1 = open(config_file_path, 'w')
        o1.write("""{
    "model": {
        "architecture":         "PhosaurusNet",
        "input_size":           1024,
        "anchors":              [%i,%i],
        "max_box_per_image":    1000,
        "num_patches":          1,
        "filter":               [0.1,"%s/tmp_filtered"]
    }
}""" % (params['diam'], params['diam'], params['dir']))
        # Firstly, flush internal buffers
        o1.flush()

        # The written string is available in program buffer but it might not
        # actually be written to disk until the program is closed or the file
        # descriptor is closed.
        # Now, sync. all internal buffers associated with the file object with
        # disk (force write of file) using os.fsync() method
        os.fsync(o1.fileno())
        o1.close()

        o2 = open(batch_script_path, 'w')
        o2.write("""#!/bin/bash
## Job name
#SBATCH --job-name=crYOLO
## Partition name
#SBATCH --partition=sb-40
## Specify the number of nodes for your job.
#SBATCH --nodes=5
## Specify the number of CPUs per node for your job.
#SBATCH --ntasks-per-node=40
## Specify how much memory per node for your job,
#SBATCH --mem=240g
## Tell Slurm the anticipated run-time for your job, where time=DD-HH:MM:SS
#SBATCH --time=12:00:00
## Ensure we are in the correct directory so the log files are where the user expects
#SBATCH --chdir=%s

## Run:
singularity exec --bind /lsi:/lsi /lsi/groups/cryoem-workshop/shared_software/cryolo/ubuntu_cryolo_cudnn.simg cryolo_predict.py -c %s/config.json -w /lsi/groups/cryoem-workshop/shared_software/cryolo/gmodel_phosnet_20181221_loss0037.h5 -i %s/ -o %s/cryolo -t %f > %s/run.out 2> %s/run.err < /dev/null
## Cleanup
rm -rf %s/tmp_filtered""" % (
            params['dir'], params['dir'], params['dir'], params['dir'], params['thresh'], params['dir'], params['dir'], params['dir']))
        # Firstly, flush internal buffers
        o2.flush()

        # The written string is available in program buffer but it might not
        # actually be written to disk until the program is closed or the file
        # descriptor is closed.
        # Now, sync. all internal buffers associated with the file object with
        # disk (force write of file) using os.fsync() method
        os.fsync(o2.fileno())
        o2.close()

        if os.path.isfile(config_file_path):
            pass
        else:
            print("The file {} was not found.  Waiting 5 seconds before continuing...")
            time.sleep(5)

        cmd = 'sbatch {}'.format(batch_script_path)
        subprocess.Popen(cmd, shell=True).wait()

    if params['stain'] is True:
        o3 = open(config_file_path, 'w')
        o3.write("""{
    "model": {
        "architecture":         "PhosaurusNet",
        "input_size":           1024,
        "anchors":              [%i,%i],
        "max_box_per_image":    1000,
        "num_patches":          1
    }
}""" % (params['diam'], params['diam']))
        # Firstly, flush internal buffers
        o3.flush()

        # The written string is available in program buffer but it might not
        # actually be written to disk until the program is closed or the file
        # descriptor is closed.
        # Now, sync. all internal buffers associated with the file object with
        # disk (force write of file) using os.fsync() method
        os.fsync(o3.fileno())
        o3.close()

        o4 = open(batch_script_path, 'w')
        o4.write("""#!/bin/bash
## Job name
#SBATCH --job-name=crYOLO
## Partition name
#SBATCH --partition=sb-40
## Specify the number of nodes for your job.
#SBATCH --nodes=5
## Specify the number of CPUs per node for your job.
#SBATCH --ntasks-per-node=40
## Specify how much memory per node for your job,
#SBATCH --mem=240g
## Tell Slurm the anticipated run-time for your job, where time=DD-HH:MM:SS
#SBATCH --time=3:00:00
## Ensure we are in the correct directory so the log files are where the user expects
#SBATCH --chdir=%s

### Run:
singularity exec --bind /lsi:/lsi /lsi/groups/cryoem-workshop/shared_software/cryolo/ubuntu_cryolo_cudnn.simg cryolo_predict.py -c %s/config.json -w /lsi/groups/cryoem-workshop/shared_software/cryolo/gmodel_phosnet_negstain_20190226.h5 -i %s/ -o %s/cryolo -t %f > %s/run.out 2> %s/run.err < /dev/null

""" % (params['dir'], params['dir'], params['dir'], params['dir'], params['thresh'], params['dir'], params['dir']))
        # Firstly, flush internal buffers
        o4.flush()

        # The written string is available in program buffer but it might not
        # actually be written to disk until the program is closed or the file
        # descriptor is closed.
        # Now, sync. all internal buffers associated with the file object with
        # disk (force write of file) using os.fsync() method
        os.fsync(o4.fileno())
        o4.close()
        if os.path.isfile(config_file_path):
            pass
        else:
            print("The file {} was not found.  Waiting 5 seconds before continuing...")
            time.sleep(5)
        cmd = 'sbatch {}'.format(batch_script_path)
        subprocess.Popen(cmd, shell=True).wait()

    print('\ncrYOLO job submitted to the cluster. \n\nOutput particle picks can be found in:\n%s/cryolo/\n\nOutput log files are:\n%s/run.out\n%s/run.err\n' % (
        params['dir'], params['dir'], params['dir']))
