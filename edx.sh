#!/bin/bash
# Batch download script
IFS=''
while read line
do
	case "$line" in
		"") continue ;;
		\#*) continue ;;
	esac
	./edx-dl.py -u your@email.com -p password -s -o . --ignore-errors --youtube-dl-options="-f 22/best" $line
	sleep 60
done <$1
