import json

from pyspark.sql.functions import current_timestamp, lit
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from engine.glue.pydeequ.profiler import ColumnProfilerRunner

from .base_step import Step


@Step(
    type="profiling",
    props_schema={
        "type": "object",
        "properties": {
            "from": {"type": "string"},
            "database": {"type": "string"},
            "table": {"type": "string"},
            "bucketdf_name": {"type": "string"},
        },
        "required": ["from", "bucketdf_name"],
    },
)
class Profiler:
    @staticmethod
    def get_value(column_field, json_profile):
        value = json_profile.get(column_field.name)
        if value is not None:
            try:
                if column_field.dataType == DoubleType():
                    value = float(value) * 1.0
                elif column_field.dataType == IntegerType():
                    value = int(value)
                elif column_field.dataType == BooleanType():
                    value = bool(value)
                elif column_field.dataType != StringType():
                    value = None

            except ValueError:
                pass

        return value

    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        df = context.df(self.props.get("from"))

        r = ColumnProfilerRunner().onData(dataFrame=df)
        r.jvmColumnProfilerRunBuilder.withKLLProfiling()

        result = r.run()
        profiling_result = json.loads(result)

        profile_schema = StructType(
            [
                StructField("column", StringType(), False),
                StructField("dataType", StringType(), True),
                StructField("isDataTypeInferred", BooleanType(), True),
                StructField("completeness", DoubleType(), True),
                StructField("approximateNumDistinctValues", IntegerType(), True),
                StructField("mean", DoubleType(), True),
                StructField("maximum", DoubleType(), True),
                StructField("minimum", DoubleType(), True),
                StructField("sum", DoubleType(), True),
                StructField("stdDev", DoubleType(), True),
                StructField("approxQ1", DoubleType(), True),
                StructField("approxQ2", DoubleType(), True),
                StructField("approxQ3", DoubleType(), True),
            ]
        )

        rows = []
        for column_profile in profiling_result.get("columns"):
            pcts = column_profile.get("approxPercentiles", [])

            # we assume that approxQ1, approxQ2, and approxQ3 are the last 3 fields , in that order
            row = [None] * len(profile_schema.fields)
            for idx, field in enumerate(profile_schema.fields):
                if len(pcts) > 98:
                    if field.name == "approxQ1":
                        row[idx] = pcts[24]
                    elif field.name == "approxQ2":
                        row[idx] = pcts[49]
                    elif field.name == "approxQ3":  # must be field.name == "approxQ3"
                        row[idx] = pcts[74]
                    else:
                        row[idx] = Profiler.get_value(field, column_profile)
                else:
                    row[idx] = Profiler.get_value(field, column_profile)

            if row[0]:
                rows.append(row)
            else:
                print("Discard {}".format(str(row)))

        bucket_schema = StructType(
            [
                StructField("column_name", StringType(), False),
                StructField("metric_type", StringType(), False),
                StructField("value_str", StringType(), True),
                StructField("value_float", DoubleType(), True),
                StructField("count", DoubleType(), True),
                StructField("ratio", DoubleType(), True),
            ]
        )

        buckets = []
        for column_profile in profiling_result.get("columns"):
            for bucket_info in column_profile.get("histogram", []):

                if (
                    column_profile.get("dataType") == "Integral"
                    or column_profile.get("dataType") == "Fractional"
                ):
                    if bucket_info.get("value") == "NullValue":
                        bucket = [
                            column_profile.get("column"),
                            "histogram",
                            bucket_info.get("value"),
                            None,
                            float(bucket_info.get("count")),
                            float(bucket_info.get("ratio")),
                        ]
                    else:
                        bucket_value = None
                        bucket_count = None
                        bucket_ratio = None
                        try:
                            bucket_value = float(bucket_info.get("value"))
                            bucket_count = float(bucket_info.get("count"))
                            bucket_ratio = float(bucket_info.get("ratio"))
                        except:
                            print("Type Error is detected")

                        bucket = [
                            column_profile.get("column"),
                            "histogram",
                            "",
                            bucket_value,
                            bucket_count,
                            bucket_ratio,
                        ]
                    buckets.append(bucket)
                else:
                    bucket = [
                        column_profile.get("column"),
                        "category",
                        bucket_info.get("value"),
                        None,
                        float(bucket_info.get("count")),
                        float(bucket_info.get("ratio")),
                    ]
                    buckets.append(bucket)

        for column_profile in profiling_result.get("columns"):
            for percentile, value in enumerate(
                column_profile.get("approxPercentiles", [])
            ):
                bucket = [
                    column_profile.get("column"),
                    "approxPercentile",
                    "",
                    float(percentile + 1),
                    value,
                    None,
                ]
                buckets.append(bucket)

        profile_df = (
            spark.createDataFrame(data=rows, schema=profile_schema)
            .withColumnRenamed("mean", "mean_col")
            .withColumnRenamed("sum", "sum_col")
            .withColumnRenamed("stdDev", "stdDev_col")
        )

        bucket_df = (
            spark.createDataFrame(data=buckets, schema=bucket_schema)
            .withColumnRenamed("count", "count_col")
            .withColumnRenamed("column", "column_name")
        )

        current_ts = current_timestamp()
        profile_out = (
            profile_df.withColumn("timestamp", current_ts)
            .withColumn("database", lit(self.props.get("database", "")))
            .withColumn("table", lit(self.props.get("table", "")))
        )

        bucket_out = (
            bucket_df.withColumn("timestamp", current_ts)
            .withColumn("database", lit(self.props.get("database", "")))
            .withColumn("table", lit(self.props.get("table", "")))
        )

        profile_out.createOrReplaceTempView(self.name)
        context.register_df(self.name, profile_out)

        bucket_out.createOrReplaceTempView(self.props.get("bucketdf_name"))
        context.register_df(self.props.get("bucketdf_name"), bucket_out)
