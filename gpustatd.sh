#!/bin/bash
BASE=`dirname $0`
cd $BASE
while :
do
  ./gpustatd.py
done
