#!/usr/bin/env bash

if [ $# -lt 1 ]; then # $# number of arguments that were passed onto the command line (less than 1)
    echo "usage: $0 subjID_ [ subjID_ ... subjID_N ]"
    exit 1;
fi;
SubjIDs=$@ #passes every argument in the command line
if [ -f stub.html ]; then
    cat stub.html
else
    cat /BrainSuite/QC/stub.html
fi;


#if [ -f js.html ]; then
#    cat js.html
#else
#    cat /BrainSuite/QC/js.html
#fi;
