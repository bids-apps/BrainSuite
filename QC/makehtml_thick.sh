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
echo "<td><a href=$i/ThickdfsLeft.png><object data=$i/ThickdfsLeft.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"
echo "<td><a href=$i/ThickdfsRight.png><object data=$i/ThickdfsRight.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"
echo "<td><a href=$i/ThickdfsSup.png><object data=$i/ThickdfsSup.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"
echo "<td><a href=$i/ThickdfsInf.png><object data=$i/ThickdfsInf.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"
echo "</tr>"

echo "<tr>"
echo "<td style='text-align:center'>Thickness PVC (left)</td>
<td style='text-align:center'>Thickness PVC (right)</td>
<td style='text-align:center'>Thickness PVC (sup)</td>
<td style='text-align:center'>Thickness PVC (inf)</td>"
echo "</tr>"

done;

echo "</table>"

if [ -f js.html ]; then
    cat js.html
else
    cat /BrainSuite/QC/js.html
fi;
