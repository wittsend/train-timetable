#!/bin/bash
DATESTR=`date "+%A %e %B %Y - %H:%M:%S"`
echo "===[Trains to work $DATESTR]==="
#python3 trainmon.py -d mrp|grep -i -e "-----" -e "=====" -e "--> Leeds"
#python3 trainmon.py -d ses|grep -i -e "-----" -e "=====" -e "--> Leeds"
#python3 trainmon.py -a lds|grep -i -e "-----" -e "=====" -e "-->"
#python3 trainmon.py -d lds|grep -i -e "-----" -e "=====" -e "--> Chester" -e "--> Wigan"
#python3 trainmon.py -a sow|grep -i -e "-----" -e "=====" -e "--> Chester" -e "--> Wigan"

python3 trainmon.py -d mrp -a lds
python3 trainmon.py -d ses -a lds
python3 trainmon.py -d lds -a sow
