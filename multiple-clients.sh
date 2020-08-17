#!/bin/bash

MEMBERS=50
PROCESSES=20
INTERVAL=5
MODE="passthrough"

for ((c=1; c<=$PROCESSES; c++))
do
echo $c
(./f5_rest_api_pool_via_cli_script_tester.py --add --members $MEMBERS --bigip 192.168.72.245 --$MODE --user admin --poolName CHAD --poolipprefix 192.168.$c --interval $INTERVAL --password Elliott351@ &)
done