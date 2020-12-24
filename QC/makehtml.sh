#!/usr/bin/env bash

if [ $# -lt 1 ]; then # $# number of arguments that were passed onto the command line (less than 1)
    echo "usage: $0 subjID_ [ subjID_ ... subjID_N ]"
    exit 1;
fi;
SubjIDs=$@ #passes every argument in the command line
if [ -f /BrainSuite/QC/stub.html ]; then
    cat /BrainSuite/QC/stub.html
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
#echo "<td><a href=$i/bse.png><img src=$i/bse.png></a></td>"
echo "<td><a href=$i/bse.png><object data=$i/bse.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/bfc.png><img src=$i/bfc.png></a></td>"

echo "<td><a href=$i/bfc.png><object data=$i/bfc.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/pvc.png><img src=$i/pvc.png></a></td>"

echo "<td><a href=$i/pvc.png><object data=$i/pvc.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/cerebro.png><img src=$i/cerebro.png></a></td>"

echo "<td><a href=$i/cerebro.png><object data=$i/cerebro.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/cortex.png><img src=$i/cortex.png></a></td>"

echo "<td><a href=$i/cortex.png><object data=$i/cortex.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/dewisp.png><img src=$i/dewisp.png></a></td>"

echo "<td><a href=$i/dewisp.png><object data=$i/dewisp.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/dfs.png><img src=$i/dfs.png width='256' height='256'></a></td>"

echo "<td><a href=$i/dfs.png><object data=$i/dfs.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/pialmesh.png><object data=$i/pialmesh.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"
#echo "<td><a href=$i/svreg.ax.png><img src=$i/svreg.ax.png></a></td>"
#echo "<td><a href=$i/svreg.png><img src=$i/svreg.png></a></td>"
#echo "</tr>"
#
#echo "<tr>"
#echo "<td><a href=$i/inner.cortex.svreg.left.png><img src=$i/inner.cortex.svreg.left.cropped.png></a></td>"
#echo "<td><a href=$i/inner.cortex.svreg.right.png><img src=$i/inner.cortex.svreg.right.cropped.png></a></td>"
#echo "<td><a href=$i/inner.cortex.svreg.inf.png><img src=$i/inner.cortex.svreg.inf.cropped.png></a></td>"
#echo "<td><a href=$i/inner.cortex.svreg.sup.png><img src=$i/inner.cortex.svreg.sup.cropped.png></a></td>"
#echo "<td><a href=$i/inner.cortex.svreg.ant.png><img src=$i/inner.cortex.svreg.ant.cropped.png></a></td>"
#echo "<td><a href=$i/inner.cortex.svreg.pos.png><img src=$i/inner.cortex.svreg.pos.cropped.png></a></td>"
#echo "</tr>"
#
#echo "<tr>"
#echo "<td><a href=$i/pvc.left.png ><img src=$i/pvc.left.cropped.png width="250" height="250"></a></td>"
#echo "<td><a href=$i/pvc.right.png><img src=$i/pvc.right.cropped.png></a></td>"
#echo "<td><a href=$i/pvc.inf.png  ><img src=$i/pvc.inf.cropped.png></a></td>"
#echo "<td><a href=$i/pvc.sup.png  ><img src=$i/pvc.sup.cropped.png></a></td>"
#echo "<td><a href=$i/pvc.ant.png  ><img src=$i/pvc.ant.cropped.png></a></td>"
#echo "<td><a href=$i/pvc.pos.png  ><img src=$i/pvc.pos.cropped.png></a></td>"

echo "</tr>"

done;

echo "</table>"

if [ -f /BrainSuite/QC/js.html ]; then
    cat /BrainSuite/QC/js.html
else
    cat ~/js.html
fi;
