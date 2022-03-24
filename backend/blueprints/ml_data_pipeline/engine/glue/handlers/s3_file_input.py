from .base_step import Step
from .observability import StepMetric
import boto3
import re


@Step(
    type="s3",
    props_schema={
        "type": "object",
        "properties": {
            "bucket": {"type": "string"},
            "prefix": {"type": "string"},
            "multiprefix": {"type": "boolean"},
            "options": {
                "type": "object",
                "properties": {
                    "format": {"type": "string"},
                    "inferSchema": {"type": "boolean"},
                    "header": {"type": "boolean"},
                    "sep": {"type": "string"},
                    "separator": {"type": "string"},
                    "withHeader": {"type": "string"},
                },
            },
        },
        "required": ["bucket", "prefix"],
    },
)
class S3FileInput:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info(f"Inside Run Step {self.name}")
        job_name = config.args.get("JOB_NAME")

        if self.props.get("multiprefix") == True:
            client = boto3.client("s3")
            paginator = client.get_paginator("list_objects")

            result = paginator.paginate(
                Bucket=self.props.get("bucket"),
                Delimiter="/",
                Prefix=self.props.get("prefix"),
            )
            prefixes = []
            for prefix in result.search("CommonPrefixes"):
                prefix_name = prefix.get("Prefix")
                if prefix_name[-1] == '/':
                    prefix_name = prefix_name[:-1]
                if prefix_name.split("/")[0] == prefix_name:
                    prefixes.append(prefix_name)
        else:
            prefixes = [self.props.get("prefix")]

        df_list = {}

        for prefix in prefixes:

            path = f's3://{self.props.get("bucket")}/{prefix}'

            self.logger.info(f"READING {path}")
            self.logger.info(f"OPTIONS {self.props.get('options',None)}")

            connection_options = {"paths": [path]}

            read_method = self.props.get("read_method", "glue")

            if read_method == "glue":

                format_options = self.props.get("options", {})
                format_param = format_options.get("format", "csv")

                if format_param == "csv":

                    if format_options.get("header"):
                        format_options["withHeader"] = format_options.get(
                            "withHeader", format_options.get("header")
                        )
                    if format_options.get("escape"):
                        format_options["escaper"] = format_options.get(
                            "escaper", format_options.get("escape")
                        )
                    if format_options.get("sep"):
                        format_options["separator"] = format_options.get(
                            "separator", format_options.get("sep")
                        )
                    if format_options.get("format"):
                        format_options.pop("format")

                self.logger.info(f"OPTIONS {format_options}")

                df = glueContext.create_dynamic_frame.from_options(
                    connection_type="s3",
                    connection_options=connection_options,
                    format=format_param,
                    format_options=format_options,
                    transformation_ctx=format_options.get("transformation_ctx", ""),
                ).toDF()

            elif read_method == "spark":
                df = spark.read.load(path, **self.props.get("options", {}))
            else:
                raise Exception("Unknown read method {}".format(read_method))

            if self.props.get("multiprefix") == True:
                # Replace all special characters except underscore
                prefix = re.compile(r"[^a-zA-Z0-9_]").sub("", prefix)
                df.createOrReplaceTempView(self.name + "_" + prefix)
                context.register_df(self.name + "_" + prefix, df)
            else:
                df.createOrReplaceTempView(self.name)
                context.register_df(self.name, df)
            df_list[prefix] = df

            self.emit_metric(
                StepMetric(
                    name=f"{job_name}/{self.name}/count",
                    unit="NbRecord",
                    value=df.rdd.countApprox(timeout=800, confidence=0.5),
                )
            )

        context.register_df_list(self.name , df_list)
