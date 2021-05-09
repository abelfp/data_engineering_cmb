import pyspark.sql.types as T


columns_final = [
    "frequency",
    "source_type",
    "halo_id",
    "ra",
    "dec",
    "redshift",
    "flux",
]
frequencies = [
    "1.4",
    "30",
    "90",
    "148",
    "219",
    "277",
    "350",
]
all_freq_c = (["source_type", "halo_id", "ra", "dec", "redshift"] +
              [f"`f_{nu}`" for nu in frequencies])
halo_low_high_columns = [
    "redshift",
    "ra",  # right ascension [degrees]
    "dec",  # declination [degrees]
    "p_cov_i",  # of halo potential minimum in Mpc
    "p_cov_j",
    "p_cov_k",
    "v_pec_i",  # proper peculiar velocity in km/s
    "v_pec_j",
    "v_pec_k",
    "Mfof",  # in Msolar
    "Mvir",  # in Msolar
    "Rvir",  # in proper Mpc
    "M200",  # mass mean density is 200 * critical density at the cluster redshift
    "R200",  # radius within where M is 200 * critical density at the cluster redshift
    "M500",
    "R500",
    "M1500",
    "R1500",
    "M2500",
    "R2500",
]
IR_SCHEMA = T.StructType([
    T.StructField("halo_id", T.IntegerType(), True),
    T.StructField("ra", T.DoubleType(), True),  # right ascension [degrees]
    T.StructField("dec", T.DoubleType(), True),  # declination [degrees]
    T.StructField("redshift", T.DoubleType(), True),
    T.StructField("f_30", T.DoubleType(), True),  # flux [mJy] at n GHz
    T.StructField("f_90", T.DoubleType(), True),
    T.StructField("f_148", T.DoubleType(), True),
    T.StructField("f_219", T.DoubleType(), True),
    T.StructField("f_277", T.DoubleType(), True),
    T.StructField("f_350", T.DoubleType(), True),
])
RADIO_SCHEMA = T.StructType([
    T.StructField("ra", T.DoubleType(), True),  # right ascension [degrees]
    T.StructField("dec", T.DoubleType(), True),  # declination [degrees]
    T.StructField("redshift", T.DoubleType(), True),
    T.StructField("f_1.4", T.DoubleType(), True),  # flux [mJy] at n GHz
    T.StructField("f_30", T.DoubleType(), True),  # flux [mJy] at n GHz
    T.StructField("f_90", T.DoubleType(), True),
    T.StructField("f_148", T.DoubleType(), True),
    T.StructField("f_219", T.DoubleType(), True),
    T.StructField("f_277", T.DoubleType(), True),
    T.StructField("f_350", T.DoubleType(), True),
])
FINAL_SCHEMA = T.StructType([
    T.StructField("frequency", T.StringType(), False),  # [GHz]
    T.StructField("source_type", T.StringType(), False),
    T.StructField("halo_id", T.IntegerType(), True),
    T.StructField("ra", T.DoubleType(), True),  # right ascension [degrees]
    T.StructField("dec", T.DoubleType(), True),  # declination [degrees]
    T.StructField("redshift", T.DoubleType(), True),  # redshift
    T.StructField("flux", T.DoubleType(), True),  # flux [mJy]
])
HALO_LOW_HIGH_SCHEMA = T.StructType(
    [T.StructField(col, T.DoubleType(), True) for col in halo_low_high_columns]
)
