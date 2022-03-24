import boto3

from .base_step import Step
from .observability import StepMetric


@Step(
    type="materialize",
    props_schema={
        "type": "object",
        "required": ["bucket", "prefix", "database", "target", "options"],
        "properties": {
            "target": {"type": "string"},
            "path": {"type": "string"},
            "bucket": {"type": "string"},
            "prefix": {"type": "string"},
            "multiprefix": {"type": "boolean"},
            "database": {"type": "string"},
            "table": {"type": "string"},
            "out_table_name_prefix": {"type": "string"},
            "mode": {"type": "string"},
            "description": {"type": "string"},
            "options": {
                "type": "object",
                "properties": {
                    "format": {"type": "string"},
                    "header": {"type": "boolean"},
                    "delimiter": {"type": "string"},
                },
                "required": ["format"],
            },
        },
        "oneOf": [{"required": ["path"]}, {"required": ["bucket", "prefix"]}],
    },
)
class Save:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        prefix = f"{self.name} [{self.type}]"
        job_name = config.args.get("JOB_NAME")

        self.logger.info(
            f"{prefix} SAVE TO {self.props.get('database')}.{self.props.get('table')}"
        )

        multiprefix = self.props.get("multiprefix") == True

        if multiprefix:
            print(self.props.get("target"))
            df_list = context.df_list(self.props.get("target"))
            self.logger.info("********")
            self.logger.info(str(df_list))
        else:
            df_list = {self.props.get("table"): context.df(self.props.get("target"))}

        for df_name, df in df_list.items():
            self.logger.info("--------")
            self.logger.info(df_name)
            self.logger.info(str(df))
            path = ""
            if self.props.get("bucket"):
                path = f"s3://{self.props.get('bucket')}/{self.props.get('prefix')}"
                if multiprefix:
                    path = path + "/" + df_name
            elif self.props.get("path"):
                path = self.props.get("path")

            table_name_prefix = self.props.get("out_table_name_prefix", "")

            dbname = self.props.get("database")
            if dbname == "":
                table_name = f"{table_name_prefix}{df_name}"
            else:
                table_name = f"{dbname}.{table_name_prefix}{df_name}"

            if df.head(1):
                num_out_files = self.props.get("num_out_files")

                if num_out_files:
                    self.logger.info("Number of outpus files {}".format(num_out_files))
                    df_out = df.coalesce(num_out_files)
                else:
                    df_out = df

                write_mode = self.props.get("mode", "overwrite")
                writer = (
                    df_out.write.mode(write_mode)
                    .format(self.props.get("options", {}).get("format", "parquet"))
                    .option("path", path)
                    .option("header", self.props.get("header", True))
                    .option("delimiter", self.props.get("delimiter", ","))
                )
                partitions = self.props.get("partitions")

                if partitions:
                    partitions_of_table = partitions.get(df_name)
                    if multiprefix and partitions_of_table:
                        self.logger.info(
                            "Partitions by {}".format(str(partitions_of_table))
                        )
                        writer = writer.partitionBy(partitions_of_table)
                    else:
                        self.logger.info("Partitions by {}".format(str(partitions)))
                        writer = writer.partitionBy(partitions)

                self.logger.info("saveAsTable {}".format(table_name))
                writer.saveAsTable(table_name, mode=write_mode)

            if multiprefix:
                context.register_df(self.name + "_" + df_name, df)
            else:
                context.register_df(self.name, df)

            self.update_table_description(
                dbname, df_name, config, self.props.get("description")
            )
            self.emit_metric(
                StepMetric(
                    name=f"{job_name}/{self.name}/count",
                    unit="NbRecord",
                    value=df.rdd.countApprox(timeout=800, confidence=0.5),
                )
            )

    def update_table_description(self, dbname, table_name, config, description):
        if config and config.args.get("ISGLUERUNTIME") and description:

            glue = boto3.client("glue")
            table = glue.get_table(DatabaseName=dbname, Name=table_name)
            table_input = table["Table"]
            update_info = {}

            other_meta_data = [
                "LastAccessTime",
                "LastAnalyzedTime",
                "Name",
                "Owner",
                "Parameters",
                "PartitionKeys",
                "Retention",
                "StorageDescriptor",
                "TableType",
                "TargetTable",
                "ViewExpandedText",
                "ViewOriginalText",
            ]
            update_info["Description"] = description
            for md in other_meta_data:
                if table_input.get(md):
                    update_info[md] = table_input.get(md)

            glue.update_table(DatabaseName=dbname, TableInput=update_info)
        else:
            self.logger.info(
                f"update table description {dbname}, {table_name}, {description}"
            )

