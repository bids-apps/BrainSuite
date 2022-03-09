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

numstages=30

if [[ -f $OUTDIR/subjs.txt ]]; then
    ln -sf $OUTDIR/subjs.txt $WEBDIR/subjs.txt
fi;

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
for subjID in ${subjects[@]}; do
	if ((i>0)); then printf ','; fi;
	filename=$WEBDIR/${subjID}/${subjID}.state;
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
for subjID in ${subjects[@]}; do
	if ((i>0)); then printf ','; fi;
	filename=$WEBDIR/${subjID}/${subjID}.state;
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
echo '"runtime": "'${runtime}'",'
printf '"process_states": ['
local i=0;
local subjID="";
for subjID in ${subjects[@]}; do
	if ((i>0)); then printf ','; fi;
	filename=$WEBDIR/${subjID}/${subjID}.state;
	if [ -f $filename ]; then
		printf -- $(<$filename);
	else
		printf -- -1;
	fi;
	((i++))
done;
echo ']';
#echo '"end": 0'
echo '}';
}

function consolidate_states {
    local subjID="";

    for subjID in ${subjects[@]}; do
        subj_state_path=${WEBDIR}/${subjID}/
        subj_state=${subj_state_path}/${subjID}.state
        states_path=${WEBDIR}/${subjID}/${subjID}/states/
        if [ -d ${states_path} ]; then
                touch ${subj_state}
                > ${subj_state}
                for (( stage=1;stage<$((numstages+1));stage++)); do
                    if [[ -f ${states_path}/stage-${stage}.state ]]; then
                        cat ${states_path}/stage-${stage}.state >>  ${subj_state}
                    fi
                done
        fi
        subj_state_var=$(cat ${subj_state})
        echo $subj_state_var | sed -e 's/ //g' > ${subj_state}
        echo \"$(cat ${subj_state})\" > ${subj_state}
    done

}
bsjson=0;
brainsuite_run_params=false
subjlist=false
for ((outerLoop=0;outerLoop<1000;outerLoop++)); do
    if [[ -f $WEBDIR/subjs.txt ]]; then
        readarray -t subjects < $WEBDIR/subjs.txt
        nSubjs=${#subjects[@]}
        consolidate_states
    else
        nSubjs=100000
    fi

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
	    if [[ -f $WEBDIR/subjs.txt ]]; then
            readarray -t subjects < $WEBDIR/subjs.txt
            nSubjs=${#subjects[@]}
            consolidate_states
        else
            nSubjs=100000
        fi
	    echo $status > $WEBPATH
#		if [ -f $OUTDIR/QC/stop.it ]; then
#		  status=`end_jobstatus terminating`;
#		  echo $status > $WEBPATH;
#		  break; fi;
		## TODO: fix logic here
		bstates_tmp=`/jq-linux64 '.process_states | .[]' ${WEBPATH}`
		read -a bstates <<< $bstates_tmp
		while [  $brainsuite_run_params == false ]; do
		    if [[ -f $WEBDIR/subjs.txt ]]; then
                readarray -t subjects < $WEBDIR/subjs.txt
                nSubjs=${#subjects[@]}
                consolidate_states
            else
                nSubjs=100000
            fi
            status=`reset_jobstatus initializing`;
            echo $status > $WEBPATH
            chmod a+r $WEBPATH
            bstates_tmp=`/jq-linux64 '.process_states | .[]' ${WEBPATH}`
		    read -a bstates <<< $bstates_tmp
            for states in ${bstates[@]}; do
                if echo $states | grep -q L; then
                    echo 'running'
#                if test $((states)) -gt 0; then
                    cp $OUTDIR/brainsuite_run_params.json $WEBDIR
                    brainsuite_run_params=true
                fi;
            done
        done

        consolidate_states

		if (( $i % 1 == 0 )); then
	        echo $status;
	        bsjson=$((bsjson+1))
	        cp ${WEBPATH} ${WEBDIR}/brainsuite_state${bsjson}.json
	    fi
	    # TODO: change logic - as long as there are no Qs and Ls
	    allstates=$(printf "%s" "${bstates[@]}")
#		nbstates=${#bstates[@]}
#		nfin=`grep -o '111' <<< $bstates_tmp | wc -l`
#		nerr=`grep -o '404' <<< $bstates_tmp | wc -l`
#		n=$((nfin + nerr))

        /BrainSuite/QC/makehtml_main.sh $subjects > $WEBDIR/index.html
		/BrainSuite/QC/makehtml_cse.sh $subjects > $WEBDIR/cse.html
		/BrainSuite/QC/makehtml_thick.sh $subjects > $WEBDIR/thick.html
		/BrainSuite/QC/makehtml_bdp.sh $subjects > $WEBDIR/bdp.html
		/BrainSuite/QC/makehtml_svreg.sh $subjects > $WEBDIR/svreg.html
		/BrainSuite/QC/makehtml_bfp.sh $subjects > $WEBDIR/bfp.html

		status=`jobstatus running`;
		echo $status > $WEBPATH
		sleep 1;

#        if (( $n > 0 )) && (( $nSubjs > 0)); then
#            if (($n == $nSubjs)); then
#                status=`end_jobstatus terminating`
#                echo $status > $WEBPATH
#                touch $WEBDIR//stop.it;
#                echo 'Completed monitoring.';
#                break;
#            fi;
#        fi;
        n=0
        if echo $allstates | grep -q Q; then
            n=$((n + 1))
        fi
        if echo $allstates | grep -q L; then
            n=$((n + 1))
        fi
        if (( $n == 0)) ; then
            status=`end_jobstatus terminating`
            echo $status > $WEBPATH
#            touch $WEBDIR//stop.it;
            echo 'Completed monitoring.';
            break;
        fi

	done
	stopTime=`date`;
	status=`end_jobstatus finished at $stopTime`;
	echo $status > $WEBPATH
	echo 'Exiting.';
	break
#	if [ -f $WEBDIR//stop.it ]; then sleep 100; break; fi;
#	for ((i=10;i>0;i--)); do
#		echo respawning in $i;
#		status=`jobstatus finished -- respawning in $i`;
#		echo $status > $WEBPATH
#		sleep 1;
#	done;
done;

status=`end_jobstatus : process monitoring has ended.`;
echo $status > $WEBPATH

killall5 -9
