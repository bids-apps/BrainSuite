for i in {0..400}; do 
	firstfile=QC/brainsuite_state$i.json;
	if [ -f $firstfile ]; then break; fi;
done;
echo $firstfile
	
if [ -f $firstfile ]; then
	for ((j=$i; j<400; j++)); do 
		nextfile=QC/brainsuite_state$j.json;
#		echo "checking $nextfile";
		if [ -f $nextfile ]; then 
			printf "$i $j:\t"; git diff --no-index --word-diff=color --word-diff-regex=.  QC/brainsuite_state{$i,$j}.json | grep status; 
			i=$j
			firstfile=nextfile;
		fi;
	done
fi;
