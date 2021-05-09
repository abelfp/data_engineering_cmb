# Data Engineering Capstone Project - CMB Simulated Data

## CMB Data
The data processed in this package was obtained from LAMBDA - NASA. You can
learn more on the data
[here](https://lambda.gsfc.nasa.gov/simulation/tb_sim_ov.cfm#2009). The simulated
data consists of Halo and Galaxy catalogs. These files can be downloaded as
binary or ascii files. I downloaded the ascii files and uploaded them to the
S3 bucket `s3://abelfp-physics-data-raw/` in the `us-east-1` region.

The Galaxy catalogs weight over 80 GB, and the Halo Catalogs weight over 800
MB.

This package transforms the data into parquet format and loads them to a data
lake in the bucket `s3://abelfp-physics-data/data_lake/` under `cmb_simulated/`
and `halo_simulated/`. `cmb_simulated` is partitioned by `frequency` and
`source_type` since the data files were split by the type of galaxies with
Basic Infrared, High Flux Infrared, and Radio.

## Running the Data Pipelines
The pipelines run in AWS EMR, to run the pipelines, I use the AWS CLI tool for
creating the cluster, bootstraping the script, and running it through a Spark
step. You can configure the cluster hardware in the
`bin/create_submit_emr_job.sh` and you can configure any Spark setting on the
`configuration/cmb_data_steps.json`.

To run the pipelines, I need to have AWS CLI set up with a user that has
permissions to create clusters. Then I run:

```bash
$ bash bin/create_submit_emr_job.sh
```
