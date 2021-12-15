#!/usr/bin/env bash

# read a line from the prog file

while read line
do
  if [ "${line:0:1}" != "#" ]; then
    echo "# prog: $line"
    ./stredit.py $line < data.txt
  fi
done < progs.txt > results.txt

diff results.txt expected_results.txt

