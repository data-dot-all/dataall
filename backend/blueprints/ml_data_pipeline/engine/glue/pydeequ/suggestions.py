class Rules:
    """
    Constraint rules
    """

    def __init__(self, spark, _jvmRule):
        self.spark = spark
        self._jvmRule = _jvmRule

    @property
    def _jvm(self):
        return self.spark.sparkContext._jvm

    @classmethod
    def CompleteIfCompleteRule(cls, spark):
        _jvmRule = (
            spark.sparkContext._jvm.com.amazon.deequ.suggestions.rules.CompleteIfCompleteRule
        )
        return cls(spark, _jvmRule)

    @classmethod
    def RetainCompletenessRule(cls, spark):
        _jvmRule = (
            spark.sparkContext._jvm.com.amazon.deequ.suggestions.rules.RetainCompletenessRule
        )
        return cls(spark, _jvmRule)

    @classmethod
    def RetainTypeRule(cls, spark):
        _jvmRule = (
            spark.sparkContext._jvm.com.amazon.deequ.suggestions.rules.RetainTypeRule
        )
        return cls(spark, _jvmRule)

    @classmethod
    def CategoricalRangeRule(cls, spark):
        _jvmRule = (
            spark.sparkContext._jvm.com.amazon.deequ.suggestions.rules.CategoricalRangeRule
        )
        return cls(spark, _jvmRule)

    @classmethod
    def FractionalCategoricalRangeRule(cls, spark):
        _jvmRule = (
            spark.sparkContext._jvm.com.amazon.deequ.suggestions.rules.FractionalCategoricalRangeRule
        )
        return cls(spark, _jvmRule)

    @classmethod
    def NonNegativeNumbersRule(cls, spark):
        _jvmRule = (
            spark.sparkContext._jvm.com.amazon.deequ.suggestions.rules.NonNegativeNumbersRule
        )
        return cls(spark, _jvmRule)
