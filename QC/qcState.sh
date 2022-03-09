#!/usr/bin/env bash

prefix=$1
stagenum=$2
state=$3

#echo $stagenum > ${filename}.state
#cat ${filename}.state | sed "s/./${stage}/${index}"
echo $state > ${prefix}/stage-${stagenum}.state