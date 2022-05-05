import json
import logging

import boto3
from engine.glue.handlers.base_step import StepInterface, StepStatus
from engine.glue.templating import render


class Context:
    def __init__(self, **config):
        self.__dict__.update(config)
        self._dataframes = {}
        self._relations = {}
        self._dataframe_list = {}

    def register_df(self, name, df):
        """Sets or returns a named dataframe"""
        self._dataframes[name] = df

    def register_df_list(self, name, dfs):
        """Sets or returns a named dataframe"""
        self._dataframe_list[name] = dfs

    def df_names(self):
        return [name for name in self._dataframes.keys()]

    def df_list_names(self):
        return [name for name in self._dataframe_list.keys()]

    def df(self, name):
        return self._dataframes.get(name, None)

    def df_list(self, name):
        return self._dataframe_list.get(name, None)

    def ref(self, step):
        """injects ref"""

        def fn(name):
            if not self._relations.get(step.name):
                self._relations[step.name] = set()
            self._relations[step.name] = self._relations[step.name].union(set([name]))
            return name

        return fn

    def get_df_dep(self, name):
        parents = set()
        for parent in self._relations.keys():
            if name in self._relations[parent]:
                parents = parents.union(set([parent]))
        return list(parents)


class Runner:
    def __init__(self, config, spark, logger=None, glueContext=None):
        self.config = config
        self.spark = spark
        self.logger = logger or logging.getLogger()
        self.context = Context()
        self.glueContext = glueContext

    def get_step_by_name(self, name):
        candidates = [s for s in self.config.steps if s.name == "name"]
        if len(candidates):
            return candidates[0]
        return None

    def run(self):
        logger = self.logger
        logger.info("Starting Runner")
        spark = self.spark

        success = True
        step: StepInterface
        for step in self.config.steps:
            logger.info(f"{step.name} [{step.type}] STARTING")
            step.run(
                spark=spark,
                config=self.config,
                context=self.context,
                logger=self.logger,
                glueContext=self.glueContext,
            )

            if step.status == StepStatus.FAIL:
                logger.info(f"{step.name} [{step.type}] FAILED ")
                success = False
                break
            else:
                logger.info(f"{step.name} [{step.type}] SUCCESS")
                logger.info(f"{step.name} [{step.type}] WRITE  METRICS")
                for metric in step.metrics:
                    logger.info("Metrics: {}".format(metric))
                    logger.info(
                        str(
                            {
                                "namespace": "dataall",
                                "JOB_RUN_ID": self.config.args.get("JOB_RUN_ID", ""),
                                "JOB_NAME": self.config.args.get("JOB_NAME", ""),
                                "metric": metric.name,
                                "value": metric.value,
                                "unit_of_measurement": metric.unit,
                            }
                        )
                    )
            logger.info(f"{step.name} [{step.type}] DONE")

        spark.sparkContext._gateway.close()

        if success:
            logger.info("Running the sql_queries completed")
        else:
            raise Exception(f"Execution failed because of failure in step {step.name} [{step.type}]")

    def report(self):
        steps = self.dag()
        nodes = {}
        for s in steps:
            nodes[s["name"]] = s
        body = render(nodes)
        return body

    def save_report(self, bucket: str = None, key: str = None, path=None):
        body = self.report()
        if not bucket and not path:
            raise Exception("InvalidParameters")
        if path:
            with open(path, "w") as f:
                f.write(body)
        else:
            s3 = boto3.client("s3", self.config.region)
            bucket = self.config.args.get("BUCKET_NAME")
            job_id = self.config.args.get("JOB_RUN_ID")
            s3.put_object(Bucket=bucket, Key=f"reports/{job_id}/report.html", Body=body)

    def save_dag(self, bucket: str = None, key: str = None, path: str = None):
        body = json.dumps(self.dag())

        if not bucket and not path:
            raise Exception("InvalidParameters")
        if path:
            with open(path, "w") as f:
                f.write(body)
        else:
            s3 = boto3.client("s3", self.config.region)
            bucket = self.config.args.get("BUCKET_NAME")
            job_id = self.config.args.get("JOB_RUN_ID")
            s3.put_object(Bucket=bucket, Key=f"reports/{job_id}/report.html", Body=body)

    def dag(self):
        nodes = []
        for i, step in enumerate(self.config.steps):
            data = step.json(self.context)
            if i > 0:
                data["parents"] = set([self.config.steps[i - 1].name])
            else:
                data["parents"] = set([])

            parents = self.context._relations.get(step.name, [])
            if len(parents):
                data["parents"] = data["parents"].union(set(parents))

            data["parents"] = list(data["parents"])
            nodes.append(data)
        return nodes
