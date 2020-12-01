#!/usr/bin/env bash

if [ $# -lt 1 ]; then # $# number of arguments that were passed onto the command line (less than 1)
    echo "usage: $0 subjID_ [ subjID_ ... subjID_N ]"
    exit 1;
fi;
SubjIDs=$@ #passes every argument in the command line
if [ -f stub.html ]; then
    cat stub.html
else
    cat ~/stub.html
fi;
echo "<table>"
for i in $SubjIDs; do
echo "<tr>"
echo "<td><b>$i</b></td>";
echo "<td><input type='checkbox' name='subID' value=${i}> Exclude</td>"
echo "<td><input type='text' placeholder='Note' class='exReason'></td>"
echo "</tr>"

echo "<tr>"
echo "<td><a href=$i/$i.masked.png><img src=$i/$i.masked.png></a></td>"
echo "<td><a href=$i/$i.bfc.ax.png><img src=$i/$i.bfc.ax.png></a></td>"
echo "<td><a href=$i/$i.pvc.ax.png><img src=$i/$i.pvc.ax.png></a></td>"
echo "<td><a href=$i/$i.pvc.cor.png><img src=$i/$i.pvc.cor.png></a></td>"
echo "<td><a href=$i/$i.svreg.ax.png><img src=$i/$i.svreg.ax.png></a></td>"
echo "<td><a href=$i/$i.svreg.png><img src=$i/$i.svreg.png></a></td>"
echo "</tr>"

echo "<tr>"
echo "<td><a href=$i/$i.inner.cortex.svreg.left.png><img src=$i/$i.inner.cortex.svreg.left.cropped.png></a></td>"
echo "<td><a href=$i/$i.inner.cortex.svreg.right.png><img src=$i/$i.inner.cortex.svreg.right.cropped.png></a></td>"
echo "<td><a href=$i/$i.inner.cortex.svreg.inf.png><img src=$i/$i.inner.cortex.svreg.inf.cropped.png></a></td>"
echo "<td><a href=$i/$i.inner.cortex.svreg.sup.png><img src=$i/$i.inner.cortex.svreg.sup.cropped.png></a></td>"
echo "<td><a href=$i/$i.inner.cortex.svreg.ant.png><img src=$i/$i.inner.cortex.svreg.ant.cropped.png></a></td>"
echo "<td><a href=$i/$i.inner.cortex.svreg.pos.png><img src=$i/$i.inner.cortex.svreg.pos.cropped.png></a></td>"
echo "</tr>"

echo "<tr>"
echo "<td><a href=$i/$i.pvc.left.png ><img src=$i/$i.pvc.left.cropped.png></a></td>"
echo "<td><a href=$i/$i.pvc.right.png><img src=$i/$i.pvc.right.cropped.png></a></td>"
echo "<td><a href=$i/$i.pvc.inf.png  ><img src=$i/$i.pvc.inf.cropped.png></a></td>"
echo "<td><a href=$i/$i.pvc.sup.png  ><img src=$i/$i.pvc.sup.cropped.png></a></td>"
echo "<td><a href=$i/$i.pvc.ant.png  ><img src=$i/$i.pvc.ant.cropped.png></a></td>"
echo "<td><a href=$i/$i.pvc.pos.png  ><img src=$i/$i.pvc.pos.cropped.png></a></td>"

done;

echo "</table>"

if [ -f js.html ]; then
    cat js.html
else
    cat ~/js.html
fi;
