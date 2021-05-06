#!/bin/bash

sudo aws s3 cp s3://abelfp-emr-resources/scripts/configurations_galaxies.py /usr/lib/python3.7/site-packages

#spark-submit --deploy-mode cluster \
    #--conf spark.pyspark.python=/usr/bin/python3.7 \
    #--conf spark.pyspark.driver.python=/usr/bin/python3.7 \
    #--num-executors 4 --driver-memory 1G \
    #--executor-cores 1 --executor-memory 1G \
    #s3://abelfp-emr-resources/scripts/cmb_data.py
