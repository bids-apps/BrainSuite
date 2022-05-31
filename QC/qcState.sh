#!/usr/bin/env bash

prefix=$1
stagenum=$2
state=$3

echo $state > ${prefix}/stage-${stagenum}.state