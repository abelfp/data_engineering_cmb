import argparse
from functools import reduce

from pyspark import SparkContext, SparkConf
from pyspark.sql import DataFrame, SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

import configurations_galaxies as cg


def _parse_args():
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
        "--halo_data_source",
        default="halo_low_mass,halo_nbody",
        type=str,
        help="Comma , separated list of Halo data sources."
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
        "--output_location_halo",
        default="data_lake/halo_simulated/",
        type=str,
        help="Prefix to write Halo data to."
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
    """Returns SparkContext with AppName set.

    Args:
        None

    Returns:
        SparkContext: SparkContext with default configuration.
    """
    conf = SparkConf()
    conf.setAppName("CMB Simulated Data Processor")
    spark_context = SparkContext(conf=conf)
    return spark_context


def _get_spark_session():
    """Returns an individual spark session.

    Args:
        None

    Returns:
        SparkSession: SparkSession for creating DataFraes
    """
    return SparkSession.builder.getOrCreate()


def _load_all_freq_df(spark_context, spark_session, source):
    """Loads Galaxy dataset from raw data in S3 to a Pyspark DataFrame

    Args:
        spark_context (SparkContext): Current SparkContext
        spark_session (SparkSession): SparkSession to create DataFrame
        source (str): Data source for the galaxy catalog to load

    Returns:
        DataFrame: Dataframe with data from source
    """
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


def _load_halo_df(spark_context, spark_session, source):
    """Loads Halo dataset from raw data in S3 to a Pyspark DataFrame

    Args:
        spark_context (SparkContext): Current SparkContext
        spark_session (SparkSession): SparkSession to create DataFrame
        source (str): Data source for the halo catalog to load

    Returns:
        DataFrame: Dataframe with data from source
    """
    s3_path = f"s3a://{args['source_bucket']}/{source}/*"
    h_rdd = spark_context.textFile(name=s3_path)
    h_rdd = h_rdd.map(lambda x: x.split()) \
                 .map(lambda x: [float(i) for i in x])

    h_df = spark_session.createDataFrame(h_rdd, cg.HALO_LOW_HIGH_SCHEMA)
    return h_df


if __name__ == "__main__":
    args = _parse_args()
    gal_sources = args["data_source"].split(",")
    halo_sources = args["halo_data_source"].split(",")
    s3_gal_des = f"s3a://{args['dest_bucket']}/{args['output_location']}"
    s3_halo_des = f"s3a://{args['dest_bucket']}/{args['output_location_halo']}"

    sc = _get_spark_context()
    spark = _get_spark_session()

    # load halo catalogs - if needed as these might not update as often
    if halo_sources:
        h_df_ls = [_load_halo_df(sc, spark, ds) for ds in halo_sources]
        halo_df = reduce(DataFrame.unionAll, h_df_ls)
        halo_df.persist()
        halo_count = halo_df.count()

        # Quality check 1: check that we have halo data in our data frame
        assert halo_count > 0, "No Halo data present!"

        halo_df.repartition(args["num_output_files"]) \
               .write \
               .mode("overwrite") \
               .parquet(s3_halo_des)

        halo_df.unpersist()

    # load galaxy catalogs
    g_df_ls = [_load_all_freq_df(sc, spark, ds) for ds in gal_sources]
    galaxies_df = reduce(DataFrame.unionAll, g_df_ls)
    galaxies_df.persist()
    galaxy_count = galaxies_df.count()

    # Quality check 2: check that we have Galaxy data in our data frame
    assert galaxy_count > 0, "No Galaxy data present!"

    for freq in cg.frequencies:
        df = galaxies_df.withColumn("frequency", F.lit(freq)) \
                        .withColumnRenamed(f"f_{freq}", "flux") \
                        .filter(F.col("flux").isNotNull()) \
                        .select(cg.columns_final)
        df.repartition(args["num_output_files"]) \
          .write \
          .partitionBy("frequency", "source_type") \
          .mode("overwrite") \
          .parquet(s3_gal_des)

    galaxies_df.unpersist()
