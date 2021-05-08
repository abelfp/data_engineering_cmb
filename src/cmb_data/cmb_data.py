import argparse

from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

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
        type=str,
        help="Percentage % separated list of data sources."
    )
    parser.add_argument(
        "--source_bucket",
        default="abelfp-physics-data-raw",
        type=str,
        help="Bucket where data is located."
    )
    parser.add_argument(
        "--dest_bucket",
        default="abelfp-physics-data",
        type=str,
        help="Destination bucket to write data to."
    )
    parser.add_argument(
        "--output_location",
        default="data_lake/cmb_simulated/",
        type=str,
        help="Prefix to write data to."
    )
    parser.add_argument(
        "--num_output_files",
        default=80,
        type=int,
        help="Number of output files to write to."
    )
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


def _load_galaxy_df(spark_context, spark_session, source):
    s3_path = f"s3a://{args['source_bucket']}/{source}/*"
    g_rdd = spark_context.textFile(name=s3_path)
    g_rdd = g_rdd.map(lambda x: x.split()) \
                 .map(lambda x: [float(i) if i.find('.') != -1 else
                                 int(i) for i in x])
    if source == "radio_simulated":
        g_df = spark_session.createDataFrame(g_rdd, cg.RADIO_SCHEMA)
        g_df = g_df.withColumn("halo_id", F.lit(None).cast(T.IntegerType()))
    else:
        g_df = spark_session.createDataFrame(g_rdd, cg.IR_SCHEMA)
    return g_df.withColumn("source_type", F.lit(source))


def _write_galaxy_df(source_df, source, s3_dest):
    freq_ls = _get_frequency_list(source)
    for freq in freq_ls:
        df = source_df.withColumn("frequency", F.lit(freq)) \
                      .withColumnRenamed(f"f_{freq}", "flux") \
                      .select(cg.columns_f)
        df.repartition(args["num_output_files"]) \
          .write \
          .partitionBy("frequency", "source_type") \
          .mode("overwrite") \
          .parquet(s3_dest)


if __name__ == "__main__":
    args = _parse_args()
    data_sources = args["data_source"].split("%")
    s3_path_dest = f"s3a://{args['dest_bucket']}/{args['output_location']}"

    sc = _get_spark_context()
    spark = _get_spark_session()

    # process the galaxy data sources
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    for data_source in data_sources:
        galaxy_df = _load_galaxy_df(sc, spark, data_source)
        galaxy_df.persist()
        galaxy_df.count()

        _write_galaxy_df(galaxy_df, data_source, s3_path_dest)
        galaxy_df.unpersist()
