#!/bin/bash

MEMBERS=50
PROCESSES=50
INTERVAL=1
MODE="passthrough"

for ((c=1; c<=$PROCESSES; c++))
do
echo $c
sleep 2
(./f5_rest_api_pool_via_cli_script_tester.py --add --members $MEMBERS --bigip 10.193.3.154 --$MODE --user admin --poolName CHAD --poolipprefix 192.168.$c --interval $INTERVAL --password admin &)
done
