#!/bin/bash python3

from pyspark.sql import SparkSession, DataFrame

from glue.pydeequ.base import VerificationSuite
from glue.pydeequ.checks import Check
from glue.pydeequ.examples import test_data


def main():
    # SparkSession startup
    spark = (
        SparkSession.builder.master("local[*]")
        .config("spark.jars.packages", "com.amazon.deequ:deequ:1.0.3-rc2")
        .appName("constrain-example")
        .getOrCreate()
    )
    df = spark.createDataFrame(test_data)

    # Constrain verification
    r = (
        VerificationSuite(spark)
        .onData(df)
        .addCheck(
            Check(spark, "error", "examples")
            .hasSize(lambda x: x == 8)
            .isUnique("_2")
            .hasCompleteness("_2", lambda x: x >= 0.75)
            .hasUniqueness("_1", lambda x: x == 3 / 8)
            .hasDistinctness("_1", lambda x: x == 5 / 8)
            .hasUniqueValueRatio("_2", lambda x: x == 0.8)
            .hasNumberOfDistinctValues("_2", lambda x: x == 6)
            # .hasHistogram
            .hasEntropy("_3", lambda x: x > 1)
            # .hasMutualInformation('_2', '_3', lambdafx x: x > 0.5)
            .hasApproxQuantile("_2", 0.5, lambda x: x == 7)
            .hasMinLength("_1", lambda x: x == 6)
            .hasMaxLength("_3", lambda x: x == 10)
            .hasMin("_2", lambda x: x == 1)
            .hasMax("_2", lambda x: x == 20)
            .hasMean("_2", lambda x: x > 10)
            .hasSum("_2", lambda x: x > 50)
            .hasStandardDeviation("_2", lambda x: x > 5)
            .hasApproxCountDistinct("_2", lambda x: x == 5)
            .hasCorrelation("_2", "_5", lambda x: x == 1)
            .satisfies("_2 > 15", "MyCondition", lambda x: x == 0.25)
            # .hasPattern("_1", "thing([A-Z])", lambdafx x: x == 1)
            # .hasDataType("_1", "string", lambdafx x: x == 1)
            .isPositive("_2")
            .isNonNegative("_2")
            .isLessThan("_5", "_2", lambda x: x == 0.375)
            .isLessThanOrEqualTo("_5", "_2", lambda x: x == 0.375)
            .isGreaterThan("_5", "_2", lambda x: x == 0.125)
            .isGreaterThanOrEqualTo("_5", "_2", lambda x: x == 0.125)
            # .isContainedIn('_3', ['DELAYED', 'INTRANSIT'])
            .isInInterval("_5", 1.0, 50.0)
        )
        .run()
    )
    df = DataFrame(r, spark)
    df.show(df.count(), False)

    # SparkSession and Java Gateway teardown
    spark.sparkContext._gateway.close()
    spark.stop()


if __name__ == "__main__":
    main()
