#!/bin/bash
DATESTR=`date "+%A %e %B %Y - %H:%M:%S"`
echo "===[Trains from work $DATESTR]==="
# Departures from Sowerby bridge
#python3 trainmon.py -d sow|grep -i -e "--> Leeds" -e "=====" -e "-----"
# Arrivals at Leeds
#python3 trainmon.py -a lds|grep -e "Chester" -e "Wigan North " -e "=====" -e "-----"
# Departures from Leeds
#python3 trainmon.py -d lds|grep -i -e "--> Sheffield" -e "--> Doncaster" -e "====="  -e "-----"
# Arrivals at Fitz
#python3 trainmon.py -a fzw|grep -i -e "Leeds              -->" -e "====="  -e "-----"
#python3 trainmon.py -a fzw|grep -i -e "Leeds *-->" -e "====="  -e "-----"

python3 trainmon.py -d sow -a lds
python3 trainmon.py -d lds -a mrp
python3 trainmon.py -d lds -a ses
