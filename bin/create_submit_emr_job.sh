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
     --steps file:///home/$USER/projects/data_engineering_cmb/configuration/cmb_data_steps.json \
     --ec2-attributes KeyName=spark-cluster \
     --auto-terminate
