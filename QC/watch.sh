#!/bin/bash

ulimit -f 20000 -c 0
startTime=`date`;
startTimeSeconds=`date +%s`;
if [[ $# -lt 2 ]]; then
echo "usage: $0 $1 webpath outputdir"
exit 0;
fi;

WEBDIR=$1
OUTDIR=$2
#subjects=($(ls ${WEBDIR} | grep sub- ))

numstages=30

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
#printf '"subjectIDs": ['
#local j=0;
#local subjidtext="";
#for subjidtext in ${subjects[@]}; do
#    if ((j>0)); then printf ','; fi;
#    printf ${subjidtext};
#    ((j++))
#done;
#echo '],';
printf '"process_states": ['
local i=0;
local subjID="";
for subjID in ${subjects[@]}; do
    subjID=`echo "$subjID" | tr -d '"'`
	filename=$WEBDIR/${subjID}/${subjID}.state;
	if ((i>0)); then printf ','; fi;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- '"P"';
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
#printf '"subjectIDs": ['
#local j=0;
#local subjidtext="";
#for subjidtext in ${subjects[@]}; do
#    if ((j>0)); then printf ','; fi;
#    printf ${subjidtext};
#    ((j++))
#done;
#echo '],';
printf '"process_states": ['
local i=0;
local subjID="";
for subjID in ${subjects[@]}; do
    subjID=`echo "$subjID" | tr -d '"'`
	filename=$WEBDIR/${subjID}/${subjID}.state;
	if ((i>0)); then printf ','; fi;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- '"P"';
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
echo '"runtime": "'${runtime}'",'
#printf '"subjectIDs": ['
#local j=0;
#local subjidtext="";
#for subjidtext in ${subjects[@]}; do
#    if ((j>0)); then printf ','; fi;
#    printf ${subjidtext};
#    ((j++))
#done;
#echo '],';
printf '"process_states": ['
local i=0;
local subjID="";
for subjID in ${subjects[@]}; do
    subjID=`echo "$subjID" | tr -d '"'`
	filename=$WEBDIR/${subjID}/${subjID}.state;
	if ((i>0)); then printf ','; fi;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- '"P"';
	fi;
	((i++))
done;
echo ']';
echo '"end": 0'
echo '}';
}

function consolidate_states {
    local subjID="";

    for subjID in ${subjects[@]}; do
        subjID=`echo "$subjID" | tr -d '"'`
        subj_state_path=${WEBDIR}/${subjID}/
        subj_state=${subj_state_path}/${subjID}.state
        states_path=${WEBDIR}/${subjID}/${subjID}/states/
        if [ -d ${states_path} ]; then
            touch ${subj_state}
            > ${subj_state}
            for (( stage=1;stage<$((numstages+1));stage++ )); do
                if [[ -f ${states_path}/stage-${stage}.state ]]; then
                    cat ${states_path}/stage-${stage}.state >>  ${subj_state}
                fi
            done
            subj_state_var=$(cat ${subj_state})
            echo $subj_state_var | sed -e 's/ //g' > ${subj_state}
            echo \"$(cat ${subj_state})\" > ${subj_state}
        fi

    done

}

bsjson=0;
begin=0;

echo Real-time QC watch initiated...
    while [ $begin -eq 0 ] ; do

        echo "Checking queued subjects..."

        if [[ -f $WEBDIR/subjectIDs.json ]]; then
            subjects_tmp=`/jq-linux64 '.subjects | .[]' ${WEBDIR}/subjectIDs.json`
            read -a subjects <<< $subjects_tmp
            echo "QCing ${#subjects[@]} subjects..."
            if [ ${#subjects[@]} > 0 ]; then
                status=`reset_jobstatus initializing`;
                echo $status;
                echo $status > $WEBPATH
                chmod a+r $WEBPATH
                for subjID in ${subjects[@]}; do
                    subjID=`echo "$subjID" | tr -d '"'`
                    subj_state_path=${WEBDIR}/${subjID}/
                    subj_state=${subj_state_path}/${subjID}.state
                    states_path=${WEBDIR}/${subjID}/${subjID}/states/
                    if [ -d ${states_path} ]; then
                        begin=1
                    fi
                done
            fi
        fi
        sleep 10
    done

for (( outerLoop=0;outerLoop<1000;outerLoop++ )); do

    consolidate_states
	status=`jobstatus running`;
    echo $status;
	echo $status > $WEBPATH

	startTime=`date`;
	startTimeSeconds=`date +%s`;
	

#    cp ${WEBPATH} ${WEBDIR}/brainsuite_state${bsjson}.json
	for ((i=0;i<100000;i++)); do
	    consolidate_states
	    status=`jobstatus running`;
	    if (( $i % 60 == 0 )); then
	        echo $status
	    fi
	    echo $status > $WEBPATH
		bstates_tmp=`/jq-linux64 '.process_states | .[]' ${WEBPATH}`
		read -a bstates <<< $bstates_tmp

#		if (( $i % 1 == 0 )); then
#	        echo $status;
#	        bsjson=$((bsjson+1))
#	        cp ${WEBPATH} ${WEBDIR}/brainsuite_state${bsjson}.json
#	    fi
	    allstates=$(printf "%s" "${bstates[@]}")

		status=`jobstatus running`;
		echo $status > $WEBPATH
		sleep 1;
        n=0
        if echo $allstates | grep -q Q; then
            n=$((n + 1))
        fi
        if echo $allstates | grep -q L; then
            n=$((n + 1))
        fi
        if echo $allstates | grep -q P; then
            n=$((n + 1))
        fi
        if (( $n == 0)) && (( ${#subjects[@]} == ${#bstates[@]} )); then
            status=`end_jobstatus terminating`
            echo $status > $WEBPATH
            echo 'Completed monitoring.';
            break;
        fi

	done
	stopTime=`date`;
	status=`end_jobstatus finished at $stopTime`;
	echo $status > $WEBPATH
	echo 'Exiting.';
	break

done;

status=`end_jobstatus process monitoring has ended.`;
echo $status > $WEBPATH

killall5 -9
