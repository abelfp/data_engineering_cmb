#!/bin/bash

NUM_EXECUTORS=1
EXECUTOR_CORE=5
EXECUTOR_MEMORY="8gb"

while getopts n:c:m: option
do
    case "${option}"
        in
        n) NUM_EXECUTORS=${OPTARG};;
        c) EXECUTOR_CORE=${OPTARG};;
        n) EXECUTOR_MEMORY=${OPTARG};;
    esac
done

echo "NUM_EXECUTORS $NUM_EXECUTORS"
echo "EXECUTOR_CORE $EXECUTOR_CORE"
echo "EXECUTOR_MEMORY $EXECUTOR_MEMORY"

spark-submit --deploy-mode cluster --jars {jars} \
    --conf {spark_configs} \
    --py-files {files} \
    --num_executors $NUM_EXECUTORS --driver-memory 12g \
    --executor-cores $EXECUTOR_CORES --executor_memory $EXECUTOR_MEMORY \
    s3://abelfp-emr-resources/scripts/cmb_data.py --arg1 val1
