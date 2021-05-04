import argparse
import ast

from pyspark.sql import DataFrame
import pyspark.sql.functions as F

# custom modules


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
        default="infrared_basic_simulated",
        choices={"infrared_basic_simulated"},
        type=str
    )

    # add other if necessary
    args = vars(parser.parse_args())  # return dict of arguments
    return args

