#!/bin/bash
startTime=`date`;
startTimeSeconds=`date +%s`;
if [[ $# -lt 2 ]]; then
echo "usage: $0 $1 webpath outputdir"
exit 0;
fi;

WEBDIR=$1
OUTDIR=$2
#subjects=($(ls ${WEBDIR} | grep sub- ))

readarray -t subjects < $WEBDIR/subjs.txt
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
	filename=$WEBDIR/$subjID/$subjID.state;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- -1;
	fi;
	((i++))
done;
echo '],';
echo '"end": 0'
echo '}';
}

function end_jobstatus {
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
	filename=$WEBDIR/$subjID/$subjID.state;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- -1;
	fi;
	((i++))
done;
echo '],';
echo '"end": 1'
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
#printf '"process_states": ['
#local subjID="";
#for subjID in $subjects; do
#	local filename=$OUTDIR/QC/$subjID/$subjID.state;
#	printf -- -1 > $filename;
#done;
#local i=0;
#for ((i=1;i<$nSubjs;i++)); do
#	printf ',-1';
#done;
#echo ']';
echo '}';
}

bsjson=0;
cp $OUTDIR/brainsuite_run_params_date.json $WEBDIR

for ((outerLoop=0;outerLoop<1000;outerLoop++)); do

	status=`reset_jobstatus initializing`;
	echo $status;
	echo $status > $WEBPATH
	chmod a+r $WEBPATH


	startTime=`date`;
	startTimeSeconds=`date +%s`;
	
    status=`jobstatus running`;
    echo $status;
    cp ${WEBPATH} ${WEBDIR}/brainsuite_state${bsjson}.json
	for ((i=0;i<100000;i++)); do
	    echo $status > $WEBPATH
#		if [ -f $OUTDIR/QC/stop.it ]; then
#		  status=`end_jobstatus terminating`;
#		  echo $status > $WEBPATH;
#		  break; fi;
		## TODO: fix logic here
		bstates_tmp=`/jq-linux64 '.process_states | .[]' ${WEBPATH}`
		read -a bstates <<< $bstates_tmp
		if (( $i % 60 == 0 )); then
	        echo $status;
	        bsjson=$((bsjson+1))
	        cp ${WEBPATH} ${WEBDIR}/brainsuite_state${bsjson}.json
	    fi
		nbstates=${#bstates[@]}
		nfin=`grep -o '111' <<< $bstates_tmp | wc -l`
		nerr=`grep -o '404' <<< $bstates_tmp | wc -l`
		n=$((nfin + nerr))

        /BrainSuite/QC/makehtml_main.sh $subjects > $WEBDIR/index.html
		/BrainSuite/QC/makehtml_cse.sh $subjects > $WEBDIR/cse.html
		/BrainSuite/QC/makehtml_thick.sh $subjects > $WEBDIR/thick.html
		/BrainSuite/QC/makehtml_bdp.sh $subjects > $WEBDIR/bdp.html
		/BrainSuite/QC/makehtml_svreg.sh $subjects > $WEBDIR/svreg.html
		/BrainSuite/QC/makehtml_bfp.sh $subjects > $WEBDIR/bfp.html

		status=`jobstatus running`;
		echo $status > $WEBPATH
		sleep 1;

		if (($n == $nSubjs)); then
			status=`end_jobstatus terminating`
			echo $status > $WEBPATH
			touch $WEBDIR//stop.it;
			echo 'Completed monitoring.';
			break;
		fi;

	done
	stopTime=`date`;
	status=`end_jobstatus finished at $stopTime`;
	echo $status > $WEBPATH
	echo 'Exiting.';
	if [ -f $WEBDIR//stop.it ]; then sleep 100; break; fi;
#	for ((i=10;i>0;i--)); do
#		echo respawning in $i;
#		status=`jobstatus finished -- respawning in $i`;
#		echo $status > $WEBPATH
#		sleep 1;
#	done;
done;

status=`end_jobstatus : process monitoring has ended.`;
echo $status > $WEBPATH
