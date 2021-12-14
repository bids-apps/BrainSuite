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
#echo "<td><a href=$i/svreglabel.png><img src=$i/svreglabel.png></a></td>"
echo "<td><a href=$i/svregLabel.png><object data=$i/svregLabel.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/svregLabelCor.png><object data=$i/svregLabelCor.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/svregLabelSag.png><object data=$i/svregLabelSag.png type='image/png'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"




#echo "<td><a href=$i/svregsurf.png><img src=$i/svregsurf.png></a></td>"

echo "<td><a href=$i/SVREGdfsLeft.png><object data=$i/SVREGdfsLeft.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/SVREGdfsRight.png><object data=$i/SVREGdfsRight.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/SVREGdfsInf.png><object data=$i/SVREGdfsInf.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/SVREGdfsSup.png><object data=$i/SVREGdfsSup.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/SVREGdfsAnt.png><object data=$i/SVREGdfsAnt.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "<td><a href=$i/SVREGdfsPos.png><object data=$i/SVREGdfsPos.png type='image/png' width='250'></a>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'></object></td>"

echo "</tr>"

echo "<tr>"
echo "<td style='text-align:center'>BFC + SVReg Label (axial)</td>
<td style='text-align:center'>BFC + SVReg Label (coronal)</td>
<td style='text-align:center'>BFC + SVReg Label (sagittal)</td>
<td style='text-align:center'>SVReg Mid Cortex (left)</td>
<td style='text-align:center'>SVReg Mid Cortex (right)</td>
<td style='text-align:center'>SVReg Mid Cortex (inferior)</td>
<td style='text-align:center'>SVReg Mid Cortex (superior)</td>
<td style='text-align:center'>SVReg Mid Cortex (anterior)</td>
<td style='text-align:center'>SVReg Mid Cortex (posterior)</td>"
echo "</tr>"

done;

echo "</table>"

if [ -f js.html ]; then
    cat js.html
else
    cat /BrainSuite/QC/js.html
fi;
