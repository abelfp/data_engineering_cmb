#!/bin/bash

aws s3 cp ~/projects/data_engineering_cmb/bin/bootstrap_cmb.sh s3://abelfp-emr-resources/bootstrap/bootstrap_cmb.sh
aws s3 cp ~/projects/data_engineering_cmb/src/cmb_data/cmb_data.py s3://abelfp-emr-resources/scripts/cmb_data.py
aws s3 cp ~/projects/data_engineering_cmb/configuration/configurations_galaxies.py s3://abelfp-emr-resources/scripts/configurations_galaxies.py

aws emr create-cluster \
     --name "CMB Data Processor" \
     --use-default-roles \
     --release-label emr-6.2.0 \
     --instance-type m5.xlarge \
     --instance-count 3 \
     --bootstrap-actions Path="s3://abelfp-emr-resources/bootstrap/bootstrap_cmb.sh" \
     --applications Name=Spark \
     --steps Type=Spark,Name="Spark Program",ActionOnFailure=TERMINATE_CLUSTER,Args=[--conf,spark.pyspark.python=/usr/bin/python3.7,--conf,spark.pyspark.driver.python=/usr/bin/python3.7,s3://abelfp-emr-resources/scripts/cmb_data.py] \
     --ec2-attributes KeyName=spark-cluster \
     --auto-terminate
