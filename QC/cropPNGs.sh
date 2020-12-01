#!/usr/bin/env bash

WEBPATH=$1
fullID=$2

cd $WEBPATH

convert ${fullID}/${fullID}.pvc.inf.png -trim -gravity center -background black -extent 256x256 +repage   ${fullID}/${fullID}.pvc.inf.cropped.png ; 
convert ${fullID}/${fullID}.pvc.sup.png -trim -gravity center -background black -extent 256x256 +repage   ${fullID}/${fullID}.pvc.sup.cropped.png ; 
convert ${fullID}/${fullID}.pvc.right.png -trim -gravity center -background black -extent 256x256 +repage ${fullID}/${fullID}.pvc.right.cropped.png ; 
convert ${fullID}/${fullID}.pvc.left.png -trim -gravity center -background black -extent 256x256 +repage  ${fullID}/${fullID}.pvc.left.cropped.png ; 
convert ${fullID}/${fullID}.pvc.ant.png -trim -gravity center -background black -extent 256x256 +repage ${fullID}/${fullID}.pvc.ant.cropped.png ; 
convert ${fullID}/${fullID}.pvc.pos.png -trim -gravity center -background black -extent 256x256 +repage ${fullID}/${fullID}.pvc.pos.cropped.png ; 


convert ${fullID}/${fullID}.inner.cortex.svreg.inf.png -trim -gravity center -background black -extent 256x256 +repage   ${fullID}/${fullID}.inner.cortex.svreg.inf.cropped.png ; 
convert ${fullID}/${fullID}.inner.cortex.svreg.sup.png -trim -gravity center -background black -extent 256x256 +repage   ${fullID}/${fullID}.inner.cortex.svreg.sup.cropped.png ; 
convert ${fullID}/${fullID}.inner.cortex.svreg.right.png -trim -gravity center -background black -extent 256x256 +repage ${fullID}/${fullID}.inner.cortex.svreg.right.cropped.png ; 
convert ${fullID}/${fullID}.inner.cortex.svreg.left.png -trim -gravity center -background black -extent 256x256 +repage  ${fullID}/${fullID}.inner.cortex.svreg.left.cropped.png ; 
convert ${fullID}/${fullID}.inner.cortex.svreg.ant.png -trim -gravity center -background black -extent 256x256 +repage  ${fullID}/${fullID}.inner.cortex.svreg.ant.cropped.png ; 
convert ${fullID}/${fullID}.inner.cortex.svreg.pos.png -trim -gravity center -background black -extent 256x256 +repage  ${fullID}/${fullID}.inner.cortex.svreg.pos.cropped.png ; 