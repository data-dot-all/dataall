import copy

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp

from engine.glue.pydeequ.base import VerificationSuite
from engine.glue.pydeequ.checks import Check, is_one

from .base_step import Step


@Step(
    type="deequ",
    props_schema={
        "type": "object",
        "properties": {
            "from": {"type": "string"},
            "checkgroups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "checkgroup": {"type": "string"},
                        "error_level": {"type": "string", "enum": ["error", "warning"]},
                        "checks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "check": {
                                        "type": "string",
                                        "enum": [
                                            "hasCompleteness",
                                            "isUnique",
                                            "hasUniqueness",
                                            "hasDistinctness",
                                            "hasUniqueValueRatio",
                                            "hasApproxQuantile",
                                            "hasMinLength",
                                            "hasMaxLength",
                                            "hasMin",
                                            "hasMax",
                                            "hasMean",
                                            "hasSum",
                                            "hasStandardDeviation",
                                            "hasApproxCountDistinct",
                                            "hasCorrelation",
                                            "satisfies",
                                            "hasPattern",
                                            "hasDataType",
                                            "isPositive",
                                            "isNonNegative",
                                            "isLessThan",
                                            "isLessThanOrEqualTo",
                                            "isGreaterThan",
                                            "isGreaterThanOrEqualTo",
                                            "isContainedIn",
                                            "all_between",
                                            "have_completeness",
                                            "all_positives",
                                            "all_non_negatives",
                                            "hasCorrelation",
                                        ],
                                    },
                                    "params": {"type": "object"},
                                },
                            },
                        },
                    },
                },
            },
        },
    },
)
class Verification:
    @staticmethod
    def assertion_factory(assertion):
        op = assertion.get("op", "eq")
        v = assertion.get("value", 100)
        min_value = assertion.get("lowerBound", 0)
        max_value = assertion.get("upperBound", 1)

        if op == "eq":
            return lambda x: x == v
        if op == "gt":
            return lambda x: x > v
        if op == "gte":
            return lambda x: x >= v
        if op == "neq":
            return lambda x: x != v
        if op == "lt":
            return lambda x: x < v
        if op == "lte":
            return lambda x: x <= v
        if op == "between":
            return lambda x: x >= min_value and x <= max_value

    @staticmethod
    def is_derived_check(check_name):
        return check_name in {
            "all_between",
            "have_completeness",
            "all_positives",
            "all_non_negatives",
        }

    @staticmethod
    def check_from_params(check, current_check):
        check_name = current_check.get("check")
        params = current_check.get("params", {})
        col_names = params.get("columns")
        assertion = params.get("assertion")

        if assertion:
            assertion_function = Verification.assertion_factory(assertion)
        else:
            assertion_function = is_one

        if check_name == "all_between":
            lower_bound = params.get("lowerBound", 0)
            upper_bound = params.get("upperBound", 1)
            null_value = params.get("null_value", "keep")

            for col_name in col_names:

                constraint = "{} >= {} AND {} <= {}".format(
                    col_name, lower_bound, col_name, upper_bound
                )

                if null_value == "discard":
                    constraint = "({} IS NULL) OR ({})".format(col_name, constraint)

                check = check.satisfies(
                    constraint,
                    "Is between {}:{}-{} ".format(col_name, lower_bound, upper_bound),
                    assertion_function,
                )
        elif check_name == "have_completeness":
            for col_name in col_names:
                check = check.hasCompleteness(col_name, assertion_function)
        elif check_name == "all_positives":
            for col_name in col_names:
                check = check.isPositive(col_name, assertion_function)
        elif check_name == "all_non_negatives":
            for col_name in col_names:
                check = check.isNonNegative(col_name, assertion_function)
        return check

    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")

        df = context.df(self.props.get("from"))

        suite = VerificationSuite(spark).onData(dataFrame=df)

        for check_group in self.props.get("checkgroups"):
            check = Check(
                spark,
                check_group.get("error_level", "warning"),
                check_group.get("checkgroup", self.name),
            )

            for check_item in check_group.get("checks"):
                cpy = copy.deepcopy(check_item)

                check_name = cpy.get("check")

                if Verification.is_derived_check(check_name):
                    check = Verification.check_from_params(check, cpy)
                else:
                    if check_item.get("params", {}).get("assertion"):
                        cpy["params"]["assertion"] = Verification.assertion_factory(
                            check_item["params"].get("assertion", {})
                        )

                    check = getattr(check, cpy.get("check"))(**cpy.get("params"))
            suite.addCheck(check)

        result = suite.run()

        result_raw = DataFrame(result, spark)
        out = result_raw.withColumn("timestamp", current_timestamp())

        out.createOrReplaceTempView(self.name)
        context.register_df(self.name, out)
