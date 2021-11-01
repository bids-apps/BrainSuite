#!/usr/bin/env bash

args=("$@")
i=${#args[*]}
inputFile="${args[0]}"
rois="${args[@]:1:$i}"

python /BrainSuite/QC/makeMask.py $inputFile --roi $rois
