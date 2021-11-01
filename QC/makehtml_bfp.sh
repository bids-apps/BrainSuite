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
echo "<td><a href=$i/ssim.png><object data=$i/ssim.png type='image/png' width='250'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/mco.png><object data=$i/mco.png type='image/png' width='250'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/fa_pvc.png><img src=$i/fa_pvc.png></a></td>"
echo "<td><a href=$i/Func2T1.png><object data=$i/Func2T1.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

#echo "<td><a href=$i/fa.png><img src=$i/fa.png></a></td>"

echo "<td><a href=$i/PreCorrFunc.png><object data=$i/PreCorrFunc.png type='image/png' width='250'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/PreCorrFuncSag.png><object data=$i/PreCorrFuncSag.png type='image/png' width='250'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/PostCorrFunc.png><object data=$i/PostCorrFunc.png type='image/png' width='250'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/PostCorrFuncSag.png><object data=$i/PostCorrFuncSag.png type='image/png' width='250'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<tr>"
echo "<td style='text-align:center'>SSIM</td><td style='text-align:center'>MCO</td><td style='text-align:center'>FUNC2T1 T1 MASK</td><td style='text-align:center'>PRECORRECT</td><td style='text-align:center'>PRECORRECT</td><td style='text-align:center'>POSTCORRECT</td><td style='text-align:center'>POSTCORRECT</td>"
echo "</tr>"


echo "</tr>"

done;

echo "</table>"

if [ -f js.html ]; then
    cat js.html
else
    cat /BrainSuite/QC/js.html
fi;
