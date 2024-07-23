#!/bin/bash
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
#SBATCH --account=an-tr043
#SBATCH --output=isp_job_script_output.txt

# add modules
module load python/3.11.5

# create virtual env to load necessary libraries/modules
virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip

pip install --no-index pandas numpy dask

# run clean_dataset python script
python clean_dataset.py
