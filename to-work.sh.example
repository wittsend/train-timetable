#!/bin/bash
DATESTR=`date "+%A %e %B %Y - %H:%M:%S"`
echo "===[Trains to work $DATESTR]==="
python3 trainmon.py -a mrp|grep -e "--> Leeds" -e "-----" -e "=====" -e ""
python3 trainmon.py -a ses|grep -e "--> Leeds" -e "-----" -e "=====" -e ""
python3 trainmon.py -d lds|grep -e "--> Wigan" -e "--> Chester" -e "-----" -e "=====" -e ""
