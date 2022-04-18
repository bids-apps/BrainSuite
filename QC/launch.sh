#!/bin/bash
if [[ "$HOSTNAME" != "clogin01.bmap.ucla.edu" ]]; then
	PORT=8086
	if (($#>0)); then PORT=$1; fi;
	if ps -e |grep -v grep| grep "http.server $PORT"; then
		echo "It looks like a server is already running on port $PORT.";
		echo "If this server is not configured for this directory, consider:";
		echo "1) killing that process and restarting"
		echo "OR"
		echo "2) using a different port via, e.g., "
		echo $(basename $0) 8081
	else
		python3 -m http.server $PORT >& web.log &
		sleep 1
	fi
	open http://127.0.0.1:$PORT
fi

Interval=0.5
Interval=1
# run simulator
for k in {1..1000}; do
	for i in {0..400}; do 
		if [ -f QC/brainsuite_state$i.json ]; then
			cp QC/brainsuite_state$i.json QC/brainsuite_state.json
			echo $k . $i
			sleep $Interval; 
		fi
	done
	echo restartng loop
	sleep 4; 
done
