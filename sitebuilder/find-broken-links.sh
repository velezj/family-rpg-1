#!/usr/bin/env bash

#WAIT=3
#BASEURL=http://localhost:8000/march-2021/
BASEURL=http://localhost:1313/

OUTPREFIX=check-links

LOGFILE="$OUTPREFIX/check-links-logfile.log"
FOUNDFILE="$OUTPREFIX/broken-links.txt"

echo "reseting output prefix '$OUTPREFIX'"
rm -rf "$OUTPREFIX"
mkdir -p "$OUTPREFIX"

echo "Crawling $BASEURL..."
# used to have --page-requisites 
wget --recursive --trust-server-names -N --no-host-directories --output-file "$LOGFILE" --directory-prefix "$OUTPREFIX" --level inf "$BASEURL"
echo "done crawling $BASEURL, log at $LOGFILE"

grep --with-filename -B4 -i "error" "$LOGFILE" | grep "http" > "$FOUNDFILE"

cat "$FOUNDFILE"
