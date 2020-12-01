#!/usr/bin/env bash

VP=/opt/BrainSuite${BrainSuiteVersion}/volblend
RENDER=/opt/BrainSuite${BrainSuiteVersion}/dfsrender

WEBPATH=$1
data=$2
output=$3
ID=$4
fullID=$5
ses=$6

umask a+r,a+x

SubjID=sub-${ID}
WEBDIR=$WEBPATH/${fullID}
install -d $WEBDIR

cd ${output}/${fullID}/anat/

if [ -z ${ses+z} ]; then
    ses='/'
else
    ses=ses-${ses};
fi

pdir=${data}/${ses}/${SubjID}/anat/


$VP --view 3 -i ${pdir}/${SubjID}_T1w.nii.gz -m ${SubjID}_T1w.mask.nii.gz -o ${WEBDIR}/${SubjID}.masked.png
$VP --view 2 -i ${SubjID}_T1w.bfc.nii.gz -o ${WEBDIR}/${SubjID}.wm.png  -m ${SubjID}_T1w.cortex.scrubbed.mask.nii.gz
$VP --view 1 -i ${SubjID}_T1w.bfc.nii.gz -o $WEBDIR/${SubjID}.bfc.ax.png
$VP --view 1 -i ${SubjID}_T1w.bfc.nii.gz -o ${WEBDIR}/${SubjID}.svreg.ax.png -l ${SubjID}_T1w.svreg.label.nii.gz \
-x /opt/BrainSuite${BrainSuiteVersion}//labeldesc/brainsuite_labeldescriptions_14May2014.xml
$VP --view 2 -i ${SubjID}_T1w.bfc.nii.gz -o ${WEBDIR}/${SubjID}.svreg.png -l ${SubjID}_T1w.svreg.label.nii.gz \
-x /opt/BrainSuite${BrainSuiteVersion}//labeldesc/brainsuite_labeldescriptions_14May2014.xml
$VP --view 2 -i ${SubjID}_T1w.bfc.nii.gz -o ${WEBDIR}/${SubjID}.pvc.cor.png -l ${SubjID}_T1w.pvc.label.nii.gz \
    -x /opt/BrainSuite${BrainSuiteVersion}//labeldesc/brainsuite_labeldescriptions_14May2014.xml
$VP --view 1 -i ${SubjID}_T1w.bfc.nii.gz -o ${WEBDIR}/${SubjID}.pvc.ax.png -l ${SubjID}_T1w.pvc.label.nii.gz \
-x /opt/BrainSuite${BrainSuiteVersion}//labeldesc/brainsuite_labeldescriptions_14May2014.xml

$RENDER -s ${SubjID}_T1w.pvc-thickness_0-6mm.mid.cortex.dfs -o $WEBDIR/${SubjID}.pvc.sup.png --sup
$RENDER -s ${SubjID}_T1w.pvc-thickness_0-6mm.mid.cortex.dfs -o $WEBDIR/${SubjID}.pvc.inf.png --inf
$RENDER -s ${SubjID}_T1w.pvc-thickness_0-6mm.mid.cortex.dfs -o $WEBDIR/${SubjID}.pvc.left.png --left
$RENDER -s ${SubjID}_T1w.pvc-thickness_0-6mm.mid.cortex.dfs -o $WEBDIR/${SubjID}.pvc.right.png --right
$RENDER -s ${SubjID}_T1w.pvc-thickness_0-6mm.mid.cortex.dfs -o $WEBDIR/${SubjID}.pvc.ant.png --ant
$RENDER -s ${SubjID}_T1w.pvc-thickness_0-6mm.mid.cortex.dfs -o $WEBDIR/${SubjID}.pvc.pos.png --pos

$RENDER -s ${SubjID}_T1w.right.inner.cortex.svreg.dfs ${SubjID}_T1w.left.inner.cortex.svreg.dfs \
-o $WEBDIR/${SubjID}.inner.cortex.svreg.sup.png --sup
$RENDER -s ${SubjID}_T1w.right.inner.cortex.svreg.dfs ${SubjID}_T1w.left.inner.cortex.svreg.dfs \
-o $WEBDIR/${SubjID}.inner.cortex.svreg.inf.png --inf
$RENDER -s ${SubjID}_T1w.right.inner.cortex.svreg.dfs ${SubjID}_T1w.left.inner.cortex.svreg.dfs \
-o $WEBDIR/${SubjID}.inner.cortex.svreg.left.png --left
$RENDER -s ${SubjID}_T1w.right.inner.cortex.svreg.dfs ${SubjID}_T1w.left.inner.cortex.svreg.dfs \
-o $WEBDIR/${SubjID}.inner.cortex.svreg.right.png --right
$RENDER -s ${SubjID}_T1w.right.inner.cortex.svreg.dfs ${SubjID}_T1w.left.inner.cortex.svreg.dfs \
-o $WEBDIR/${SubjID}.inner.cortex.svreg.ant.png --ant
$RENDER -s ${SubjID}_T1w.right.inner.cortex.svreg.dfs ${SubjID}_T1w.left.inner.cortex.svreg.dfs \
-o $WEBDIR/${SubjID}.inner.cortex.svreg.pos.png --pos
