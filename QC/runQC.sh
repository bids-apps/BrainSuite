#!/usr/bin/env bash

# first generate thumbnails
WEBPATH=$1
data=$2
output=$3
ID=$4
fullID=$5
ses=$6

QC=/BrainSuite/QC/generateQC.sh
cropPNG=/BrainSuite/QC/cropPNG.sh
HTML=/BrainSuite/QC/makehtml.sh

$QC $WEBPATH $data $output $ID $fullID $ses
$cropPNG $WEBPATH $fullID

cd $WEBPATH
$HTML `ls | grep sub-` > index.html

