#!/usr/bin/env bash

#WAIT=3
BASEURL=http://localhost:8000/march-2021/

wget --recursive --page-requisites -N --no-host-directories --output-file check-links-logfile.log --directory-prefix check-links --level inf $BASEURL

grep -C2 -i "error" check-links-logfile.log | grep "http" > broken-links.txt

cat broken-links.txt
