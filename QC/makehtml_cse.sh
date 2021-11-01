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

echo "<td><a href=$i/hemilabel.png><object data=$i/hemilabel.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/cerebro.png><object data=$i/cerebro.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"


echo "<td><a href=$i/dewisp_ax.png><object data=$i/dewisp.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/dewispCor.png><object data=$i/dewispCor.png type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"


#echo "<td><a href=$i/dfs.png><img src=$i/dfs.png width='256' height='256'></a></td>"

echo "<td><a href=$i/dfsLeft.png><object data=$i/dfsLeft.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/dfsRight.png><object data=$i/dfsRight.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/dfsSup.png><object data=$i/dfsSup.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"

echo "<td><a href=$i/dfsInf.png><object data=$i/dfsInf.png width='256' height='256' type='image/png'>"
echo "<img src='http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/defaultimg.jpg'</a></object></td>"


echo "<tr>"
echo "<td style='text-align:center'>Orig + BSE Mask</td>
<td style='text-align:center'>BFC</td>
<td style='text-align:center'>PVC</td>
<td style='text-align:center'>Orig + Hemi Label </td>
<td style='text-align:center'>Orig + Cerebrum Mask</td>

<td style='text-align:center'>BFC + Dewisp (axial)</td>
<td style='text-align:center'>BFC + Dewisp (coronal)</td>
<td style='text-align:center'>Inner Cortex (left)</td>
<td style='text-align:center'>Inner Cortex (right)</td>
<td style='text-align:center'>Inner Cortex (superior)</td>
<td style='text-align:center'>Inner Cortex (inferior)</td>"
echo "</tr>"

echo "</tr>"

done;

echo "</table>"

if [ -f js.html ]; then
    cat js.html
else
    cat /BrainSuite/QC/js.html
fi;
