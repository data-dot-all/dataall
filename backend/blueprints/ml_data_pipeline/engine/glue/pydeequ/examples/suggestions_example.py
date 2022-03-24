#!/bin/bash python3

import json
from pyspark.sql import SparkSession, DataFrame

from glue.pydeequ.base import ConstraintSuggestionRunner
from glue.pydeequ.suggestions import Rules
from glue.pydeequ.examples import test_data


def main():
    # SparkSession startup
    spark = (
        SparkSession.builder.master("local[*]")
        .config("spark.jars.packages", "com.amazon.deequ:deequ:1.0.3-rc2")
        .appName("suggestions-example")
        .getOrCreate()
    )
    df = spark.createDataFrame(test_data)

    # Constrain verification
    r = (
        ConstraintSuggestionRunner(spark)
        .onData(df)
        .addConstraintRule(Rules.CategoricalRangeRule(spark))
        .run()
    )

    parsed = json.loads(r)
    print(json.dumps(parsed, indent=4))

    # SparkSession and Java Gateway teardown
    spark.sparkContext._gateway.close()
    spark.stop()


if __name__ == "__main__":
    main()
