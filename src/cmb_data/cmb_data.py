import argparse
from functools import reduce

from pyspark import SparkContext, SparkConf
from pyspark.sql import DataFrame, SparkSession
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
        help="Comma , separated list of Galaxy data sources."
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
        help="Prefix to write Galaxy data to."
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


def _load_all_freq_df(spark_context, spark_session, source):
    s3_path = f"s3a://{args['source_bucket']}/{source}/*"
    g_rdd = spark_context.textFile(name=s3_path)
    g_rdd = g_rdd.map(lambda x: x.split()) \
                 .map(lambda x: [float(i) if i.find('.') != -1 else
                                 int(i) for i in x])

    # create dataframes and account for missing halo_id in radio_simulated
    if source == "radio_simulated":
        g_df = spark_session.createDataFrame(g_rdd, cg.RADIO_SCHEMA)
        g_df = g_df.withColumn("halo_id", F.lit(None).cast(T.IntegerType()))
    else:
        g_df = spark_session.createDataFrame(g_rdd, cg.IR_SCHEMA)

    # add missing frequencies to dataset
    miss_freq_c = {f"f_{nu}" for nu in cg.frequencies} - set(g_df.columns)
    for freq_col in miss_freq_c:
        g_df = g_df.withColumn(freq_col, F.lit(None).cast(T.DoubleType()))

    return g_df.withColumn("source_type", F.lit(source)).select(cg.all_freq_c)


if __name__ == "__main__":
    args = _parse_args()
    data_sources = args["data_source"].split(",")
    s3_path_dest = f"s3a://{args['dest_bucket']}/{args['output_location']}"

    sc = _get_spark_context()
    spark = _get_spark_session()

    df_ls = [_load_all_freq_df(sc, spark, ds) for ds in data_sources]
    galaxies_df = reduce(DataFrame.unionAll, df_ls)
    galaxies_df.persist()
    galaxies_df.count()

    for freq in cg.frequencies:
        df = galaxies_df.withColumn("frequency", F.lit(freq)) \
                        .withColumnRenamed(f"f_{freq}", "flux") \
                        .filter(F.col("flux").isNotNull()) \
                        .select(cg.columns_final)
        df.repartition(args["num_output_files"]) \
          .write \
          .partitionBy("frequency", "source_type") \
          .mode("overwrite") \
          .parquet(s3_path_dest)

    galaxies_df.unpersist()
