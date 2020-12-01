#!/bin/bash
startTime=`date`;
startTimeSeconds=`date +%s`;
if [[ $# -lt 1 ]]; then
echo "usage: $0 webpath"
exit 0;
fi;

WEBDIR=$1
subjects=($(ls ${WEBDIR} | grep sub- ))

nSubjs=${#subjects[@]}

WEBPATH=${WEBDIR}/brainsuite_state.json

function timediff {
local t2=`stat -c%Y $1`;
local t1=`stat -c%Y $2`;
local delta=$((t2 - t1));
echo $delta
}

function jobstatus {
updateTime=`date`;
updateSeconds=`date +%s`
seconds=$((updateSeconds-startTimeSeconds));
runtime=`date -u -d @${seconds} +"%T"`;
echo '{'
echo '"status": "'${@}'",'
echo '"start_time": "'${startTime}'",'
echo '"update_time": "'${updateTime}'",'
echo '"runtime": "'${runtime}'",'
printf '"process_states": ['
local i=0;
local subjID="";
for subjID in $subjects; do
	if ((i>0)); then printf ','; fi;
	filename=$subjID/$subjID.state;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- -1;
	fi;
	((i++))
done;
echo ']';
echo '}';
}

function reset_jobstatus {
updateTime=`date`;
updateSeconds=`date +%s`
echo '{'
echo '"status": "'${@}'",'
echo '"start_time": "'${startTime}'",'
echo '"update_time": "'${updateTime}'",'
seconds=$((updateSeconds-startTimeSeconds));
runtime=`date -u -d @${seconds} +"%T"`;
echo '"runtime": "'${runtime}'",'
printf '"process_states": ['
local subjID="";
for subjID in $subjects; do
	local filename=$subjID/$subjID.state;
	printf -- -1 > $filename;
done;
local i=0;
for ((i=1;i<$nSubjs;i++)); do
	printf ',-1';
done;
echo ']';
echo '}';
}

for ((outerLoop=0;outerLoop<1000;outerLoop++)); do

	status=`reset_jobstatus initializing`;
	echo $status;
	echo $status > $WEBPATH
	chmod a+r $WEBPATH

	subjects=($(ls ${WEBDIR} | grep sub- ))
	nSubjs=${#subjects[@]}

	startTime=`date`;
	startTimeSeconds=`date +%s`;
	

	for ((i=0;i<10000;i++)); do
		if [ -f stop.it ]; then break; fi;
		bstates=`/jq-linux64 '.process_states | .[]' ${WEBPATH}`
		nbstates=${#bstates[@]}
		nfin=`grep -o '9' <<< $bstates | wc -l`
		nerr=`grep -o '404' <<< $bstates | wc -l`
		n=$((nfin + nerr))
		if ((n==nbstates)); then 
			break; 
		fi;
		/BrainSuite/QC/makehtml.sh $subjects > $WEBDIR/index.html
		status=`jobstatus running`;
		echo $status > $WEBPATH
		sleep 1;
	done
	stopTime=`date`;
	status=`jobstatus finished at $stopTime`;
	echo $status > $WEBPATH
	if [ -f stop.it ]; then break; fi;
	for ((i=10;i>0;i--)); do
		echo respawning in $i;
		status=`jobstatus finished -- respawning in $i`;
		echo $status > $WEBPATH
		sleep 1;
	done;
done;

status=`jobstatus : process monitoring has ended.`;
echo $status > $WEBPATH
