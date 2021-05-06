import argparse

from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

import configurations_galaxies as cg


def _parse_args() -> dict:
    """Returns a dictionary of the arguments passed to the file.
    Args:
        None
    Returns:
        dict: Dictionary of arguments passed to the file.
    """
    parser = argparse.ArgumentParser(description="Command line args for job")
    parser.add_argument(
        "--data_source",
        default="infrared_high_flux_simulated",
        choices={
            "infrared_basic_simulated",
            "infrared_high_flux_simulated",
            "radio_simulated",
        },
        type=str
    )
    parser.add_argument(
        "--source_bucket",
        default="abelfp-physics-data-raw",
        type=str
    )
    parser.add_argument(
        "--dest_bucket",
        default="abelfp-physics-data",
        type=str
    )
    parser.add_argument(
        "--output_location",
        default="data_lake/cmb_simulated/",
        type=str
    )
    parser.add_argument("--tasknum", default=10, type=int)
    # add other if necessary
    args = vars(parser.parse_args())  # return dict of arguments
    return args


def _get_spark_context():
    conf = SparkConf()
    conf.setAppName("CMB Simulated Data Processor")
    spark_context = SparkContext(conf=conf)
    return spark_context


def _get_spark_session():
    return SparkSession.builder.getOrCreate()


def _get_frequency_list(simulation_id):
    simulations_freq = {
        "infrared_basic_simulated": [
            "30",
            "90",
            "148",
            "219",
            "277",
            "350"
        ],
        "infrared_high_flux_simulated": [
            "30",
            "90",
            "148",
            "219",
            "277",
            "350"
        ],
        "radio_simulated": [
            "1.4",
            "30",
            "90",
            "148",
            "219",
            "277",
            "350"
        ],
    }
    return simulations_freq.get(simulation_id)


if __name__ == "__main__":
    args = _parse_args()
    s3_path_source = f"s3a://{args['source_bucket']}/{args['data_source']}/*"
    print(s3_path_source)
    s3_path_dest = f"s3a://{args['dest_bucket']}/{args['output_location']}"
    print(s3_path_dest)
    freq_ls = _get_frequency_list(args["data_source"])

    sc = _get_spark_context()
    spark = _get_spark_session()
    sim_rdd = sc.textFile(name=s3_path_source).coalesce(args["tasknum"])
    sim_rdd = sim_rdd.map(lambda x: x.split()) \
        .map(lambda x: [float(i) if i.find('.') != -1 else int(i) for i in x])

    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    sim_df = spark.createDataFrame(sim_rdd, cg.IR_SCHEMA)
    sim_df = sim_df.withColumn("source_type", F.lit(args["data_source"]))
    for freq in freq_ls:
        df = sim_df.withColumn("frequency", F.lit(freq)) \
                   .withColumnRenamed(f"f_{freq}", "flux")
        df = df.select(cg.columns_f)
        df.repartition(F.col("frequency"), F.col("source_type")) \
          .write \
          .partitionBy("frequency", "source_type") \
          .mode("overwrite") \
          .parquet(s3_path_dest)
