#!/bin/bash

aws s3 cp ~/projects/data_engineering_cmb/bin/bootstrap_cmb.sh s3://abelfp-emr-resources/bootstrap/bootstrap_cmb.sh
aws s3 cp ~/projects/data_engineering_cmb/src/cmb_data/cmb_data.py s3://abelfp-emr-resources/scripts/cmb_data.py
aws s3 cp ~/projects/data_engineering_cmb/configuration/configurations_galaxies.py s3://abelfp-emr-resources/scripts/configurations_galaxies.py

aws emr create-cluster \
     --name "CMB Data Processor" \
     --use-default-roles \
     --release-label emr-6.2.0 \
     --instance-type r4.xlarge \
     --instance-count 10 \
     --bootstrap-actions Path="s3://abelfp-emr-resources/bootstrap/bootstrap_cmb.sh" \
     --applications Name=Spark \
     --steps Type=Spark,Name="Spark Program",ActionOnFailure=TERMINATE_CLUSTER,Args=[--deploy-mode,cluster,--master,yarn,--conf,spark.pyspark.python=/usr/bin/python3.7,--conf,spark.pyspark.driver.python=/usr/bin/python3.7,--num-executors,14,--driver-memory,12G,--executor-cores,2,--executor-memory,18G,s3://abelfp-emr-resources/scripts/cmb_data.py,--data_source,infrared_basic_simulated] \
     --ec2-attributes KeyName=spark-cluster \
     --auto-terminate
