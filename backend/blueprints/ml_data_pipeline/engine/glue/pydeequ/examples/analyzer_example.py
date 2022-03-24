from pyspark.sql import SparkSession, DataFrame

from glue.pydeequ.base import AnalysisRunner
import glue.pydeequ.analyzers as analyzers
from glue.pydeequ.examples import test_data


def main():
    # SparkSession startup
    spark = (
        SparkSession.builder.master("local[*]")
        .config("spark.jars.packages", "com.amazon.deequ:deequ:1.0.3-rc2")
        .appName("profiler-example")
        .getOrCreate()
    )
    df = spark.createDataFrame(test_data)

    r = (
        AnalysisRunner(spark)
        .onData(df)
        .addAnalyzer(analyzers.Size())
        .addAnalyzer(analyzers.Completeness("_3"))
        .addAnalyzer(analyzers.ApproxCountDistinct("_1"))
        .addAnalyzer(analyzers.Mean("_2"))
        .addAnalyzer(analyzers.Compliance("top values", "_2 > 15"))
        .addAnalyzer(analyzers.Correlation("_2", "_5"))
        .run()
    )

    df = DataFrame(r, spark)
    df.show(df.count(), False)

    # SparkSession and Java Gateway teardown
    spark.sparkContext._gateway.close()
    spark.stop()


if __name__ == "__main__":
    main()
