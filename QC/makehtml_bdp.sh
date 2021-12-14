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

echo "<table>"
for i in $SubjIDs; do
echo "<tr>"
echo "<td><b>$i</b></td>";
echo "<td><input type='checkbox' name='subID' value=${i}> Exclude</td>"
echo "<td><input type='text' placeholder='Note' class='exReason'></td>"
echo "</tr>"

echo "<tr>"

echo "<td><a href=$i/PreCorrDWI.png><object data=$i/PreCorrDWI.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/PreCorrDWIsag.png><object data=$i/PreCorrDWIsag.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/PostCorrDWI.png><object data=$i/PostCorrDWI.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/PostCorrDWIsag.png><object data=$i/PostCorrDWIsag.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

#echo "<td><a href=$i/fa_pvc.png><img src=$i/fa_pvc.png></a></td>"
echo "<td><a href=$i/FApvc.png><object data=$i/FApvc.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

#echo "<td><a href=$i/fa.png><img src=$i/fa.png></a></td>"

echo "<td><a href=$i/FA.png><object data=$i/FA.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/colorFA.png><object data=$i/colorFA.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/mADC.png><object data=$i/mADC.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"



echo "<tr>"
echo "<td style='text-align:center'>PRECORRECT</td><td style='text-align:center'>PRECORRECT</td><td style='text-align:center'>POSTCORRECT</td><td style='text-align:center'>POSTCORRECT</td><td style='text-align:center'>FA PVC</td><td style='text-align:center'>FA</td><td style='text-align:center'>COLOR FA</td><td style='text-align:center'>mADC</td>"
echo "</tr>"


echo "</tr>"

done;

echo "</table>"

if [ -f js.html ]; then
    cat js.html
else
    cat /BrainSuite/QC/js.html
fi;
