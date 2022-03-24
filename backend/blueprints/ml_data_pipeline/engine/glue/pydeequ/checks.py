import py4j.java_gateway as jg

from engine.glue.pydeequ.exceptions import JavaClassNotFoundException
import engine.glue.pydeequ.jvm_conversions as jc


def is_one(x):
    """Helper function for default asseritons."""
    return x == 1


class Check(object):
    """
    A class representing a list of constraints that can be applied to a given
    [[org.apache.spark.sql.DataFrame]]. In order to run the checks, use the
    VerificationSuite.run to run your checks along with other Checks and
    Analysis objects. When run with VerificationSuite, Analyzers required by
    multiple checks/analysis blocks is optimized to run once.
    """

    def __init__(self, SparkSession, level="error", description=None, jvmCheck=None):
        """
        Args:
            sparkContext (pyspark.context.SparkContext): active SparkContext
            level (str): 'error' (default), 'warning'
                Assertion level of the check group. If any of the constraints
                fail this level is used for the status of the check
            description (str): The name describes the check block. Generally
                will be used to show in the logs
        """
        self.spark = SparkSession
        self._level = level
        self._description = description
        if jvmCheck:
            self.jvmCheck = jvmCheck
        else:
            deequ_check = self._jvm.com.amazon.deequ.checks.Check
            if not isinstance(deequ_check, jg.JavaClass):
                raise JavaClassNotFoundException("com.amazon.deequ.checks.Check")
            self.jvmCheck = deequ_check(
                self._jvm_level,
                self._description,
                getattr(deequ_check, "apply$default$3")(),
            )

    @property
    def _jvm(self):
        return self.spark.sparkContext._jvm

    @property
    def level(self):
        return self._level

    @property
    def description(self):
        return self._description

    @property
    def _jvm_level(self):
        if self._level == "error":
            return self._jvm.com.amazon.deequ.checks.CheckLevel.Error()
        elif self._level == "warning":
            return self._jvm.com.amazon.deequ.checks.CheckLevel.Warning()
        else:
            raise ValueError("Invalid 'level'")

    def hasSize(self, assertion):
        """
        Creates a constraint that calculates the data frame size and runs the
        assertion on it.
        Args:
            assertion (function):
        Returns:
            checks.Check object including this constraint
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasSize(
            function, getattr(self.jvmCheck, "hasSize$default$2")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isUnique(self, column):
        """
        Creates a constraint that asserts on a column uniqueness.
        Args:
            column (str): Column to run the assertion on
        Returns:
            checks.Check object including this constraint
        """
        jvmConstraint = self.jvmCheck.isUnique(
            column, getattr(self.jvmCheck, "isUnique$default$2")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasCompleteness(self, column, assertion):
        """
        Creates a constraint that asserts on a column completion.
        Uses the given history selection strategy to retrieve historical completeness values on this
        column from the history provider.

        @param column    Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasCompleteness(
            column, function, getattr(self.jvmCheck, "hasCompleteness$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasUniqueness(self, columns, assertion):
        """
        Creates a constraint that asserts on uniqueness in a single or combined set of key columns.

        @param columns Key columns
        @param assertion Function that receives a double input parameter and returns a boolean.
                         Refers to the fraction of unique values
        @param hint A hint to provide additional context why a constraint could have failed
        """
        if not isinstance(columns, list):
            # Single column is provided
            columns = [columns]
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasUniqueness(
            jc.iterable_to_scala_seq(self._jvm, columns), function
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasDistinctness(self, columns, assertion):
        """
        Creates a constraint on the distinctness in a single or combined set of key columns.

        @param columns columns
        @param assertion Function that receives a double input parameter and returns a boolean.
                         Refers to the fraction of distinct values.
        @param hint A hint to provide additional context why a constraint could have failed
        """
        if not isinstance(columns, list):
            # Single column is provided
            columns = [columns]
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasDistinctness(
            jc.iterable_to_scala_seq(self._jvm, columns),
            function,
            getattr(self.jvmCheck, "hasDistinctness$default$3")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasUniqueValueRatio(self, columns, assertion):
        """
        Creates a constraint on the unique value ratio in a single or combined set of key columns.

        @param columns columns
        @param assertion Function that receives a double input parameter and returns a boolean.
                         Refers to the fraction of distinct values.
        @param hint A hint to provide additional context why a constraint could have failed
        """
        if not isinstance(columns, list):
            # Single column is provided
            columns = [columns]
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasUniqueValueRatio(
            jc.iterable_to_scala_seq(self._jvm, columns),
            function,
            getattr(self.jvmCheck, "hasUniqueValueRatio$default$3")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasNumberOfDistinctValues(
        self, column, assertion, binningUdf=None, maxBins=None
    ):
        """
        Creates a constraint that asserts on the number of distinct values a column has.

        @param column     Column to run the assertion on
        @param assertion  Function that receives a long input parameter and returns a boolean
        @param binningUdf An optional binning function
        @param maxBins    Histogram details is only provided for N column values with top counts.
                          maxBins sets the N
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasNumberOfDistinctValues(
            column,
            function,
            getattr(self.jvmCheck, "hasNumberOfDistinctValues$default$3")(),
            getattr(self.jvmCheck, "hasNumberOfDistinctValues$default$4")(),
            getattr(self.jvmCheck, "hasNumberOfDistinctValues$default$5")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasHistogramValues(self, column, assertion, binningUdf=None, maxBins=None):
        """
        Creates a constraint that asserts on column's value distribution.

        @param column     Column to run the assertion on
        @param assertion  Function that receives a Distribution input parameter and returns a boolean.
                          E.g
                          .hasHistogramValues("att2", _.absolutes("f") == 3)
                          .hasHistogramValues("att2",
                          _.ratios(Histogram.NullFieldReplacement) == 2/6.0)
        @param binningUdf An optional binning function
        @param maxBins    Histogram details is only provided for N column values with top counts.
                          maxBins sets the N
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasHistogramValues(
            column,
            function,
            getattr(self.jvmCheck, "hasHistogramValues$default$3")(),
            getattr(self.jvmCheck, "hasHistogramValues$default$4")(),
            getattr(self.jvmCheck, "hasHistogramValues$default$5")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasEntropy(self, column, assertion):
        """
        Creates a constraint that asserts on a column entropy.

        @param column    Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint      A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasEntropy(
            column, function, getattr(self.jvmCheck, "hasEntropy$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasMutualInformation(self, columnA, columnB, assertion):
        """
        Creates a constraint that asserts on a mutual information between two columns.

        @param columnA   First column for mutual information calculation
        @param columnB   Second column for mutual information calculation
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint      A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasMutualInformation(
            columnA,
            columnB,
            function,
            getattr(self.jvmCheck, "hasMutualInformation$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasApproxQuantile(self, column, quantile, assertion):
        """
        Creates a constraint that asserts on an approximated quantile

        @param column Column to run the assertion on
        @param quantile Which quantile to assert on
        @param assertion Function that receives a double input parameter (the computed quantile)
                         and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasApproxQuantile(
            column,
            quantile,
            function,
            getattr(self.jvmCheck, "hasApproxQuantile$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasMinLength(self, column, assertion):
        """
        Creates a constraint that asserts on the minimum length of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasMinLength(
            column, function, getattr(self.jvmCheck, "hasMinLength$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasMaxLength(self, column, assertion):
        """
        Creates a constraint that asserts on the maximum length of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasMaxLength(
            column, function, getattr(self.jvmCheck, "hasMaxLength$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasMin(self, column, assertion):
        """
        Creates a constraint that asserts on the minimum of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasMin(
            column, function, getattr(self.jvmCheck, "hasMin$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasMax(self, column, assertion):
        """
        Creates a constraint that asserts on the maximum of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasMax(
            column, function, getattr(self.jvmCheck, "hasMax$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasMean(self, column, assertion):
        """
        Creates a constraint that asserts on the mean of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasMean(
            column, function, getattr(self.jvmCheck, "hasMean$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasSum(self, column, assertion):
        """
        Creates a constraint that asserts on the sum of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasSum(
            column, function, getattr(self.jvmCheck, "hasSum$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasStandardDeviation(self, column, assertion):
        """
        Creates a constraint that asserts on the standard deviation of the column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasStandardDeviation(
            column, function, getattr(self.jvmCheck, "hasStandardDeviation$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasApproxCountDistinct(self, column, assertion):
        """
        Creates a constraint that asserts on the approximate count distinct of the given column

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasApproxCountDistinct(
            column,
            function,
            getattr(self.jvmCheck, "hasApproxCountDistinct$default$3")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasCorrelation(self, columnA, columnB, assertion):
        """
        Creates a constraint that asserts on the pearson correlation between two columns.

        @param columnA   First column for correlation calculation
        @param columnB   Second column for correlation calculation
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasCorrelation(
            columnA,
            columnB,
            function,
            getattr(self.jvmCheck, "hasCorrelation$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def satisfies(self, columnCondition, constraintName, assertion):
        """
        Creates a constraint that runs the given condition on the data frame.

        @param columnCondition Data frame column which is a combination of expression and the column
                               name. It has to comply with Spark SQL syntax.
                               Can be written in an exact same way with conditions inside the
                               `WHERE` clause.
        @param constraintName  A name that summarizes the check being made. This name is being used to
                               name the metrics for the analysis being done.
        @param assertion       Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.satisfies(
            columnCondition,
            constraintName,
            function,
            getattr(self.jvmCheck, "satisfies$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def hasPattern(self, column, pattern, assertion=is_one):
        """
        Checks for pattern compliance. Given a column name and a regular expression, defines a
        Check on the average compliance of the column's values to the regular expression.

        @param column Name of the column that should be checked.
        @param pattern The columns values will be checked for a match against this pattern.
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        # function = jc.scala_function1(self.spark.sparkContext._gateway,
        #                              assertion)
        # pattern = jc.scala_regex(self.spark.sparkContext._gateway, pattern)
        # jvmConstraint = self.jvmCheck.hasPattern(
        #     column,
        #     pattern,
        #     function,
        #     getattr(self.jvmCheck, "hasPattern$default$4")(),
        #     getattr(self.jvmCheck, "hasPattern$default$5")()
        # )
        # return Check(
        #     self.spark,
        #     self.level,
        #     self.description,
        #     jvmConstraint
        # )
        pass

    def hasDataType(self, column, dataType, assertion):
        """
        Check to run against the fraction of rows that conform to the given data type.

        @param column Name of the columns that should be checked.
        @param dataType Data type that the columns should be compared against.
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        _jconstDataTypes = self._jvm.com.amazon.deequ.constraints.ConstrainableDataTypes
        dataTypes = {
            "null": _jconstDataTypes.Null(),
            "boolean": _jconstDataTypes.Boolean(),
            "string": _jconstDataTypes.String(),
            "numeric": _jconstDataTypes.Numeric(),
            "fractional": _jconstDataTypes.Fractional(),
            "integer": _jconstDataTypes.Integral(),
        }
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.hasDataType(
            column,
            dataTypes[dataType],
            function,
            getattr(self.jvmCheck, "hasDataType$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isPositive(self, column, assertion=is_one):
        """
        Creates a constraint that asserts that a column contains positive values

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.isPositive(
            column, function, getattr(self.jvmCheck, "isPositive$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isNonNegative(self, column, assertion=is_one):
        """
        Creates a constraint that asserts that a column contains no negative values

        @param column Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.isNonNegative(
            column, function, getattr(self.jvmCheck, "isNonNegative$default$3")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isLessThan(self, columnA, columnB, assertion=is_one):
        """
        Asserts that, in each row, the value of columnA is less than the value of columnB

        @param columnA Column to run the assertion on
        @param columnB Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.isLessThan(
            columnA, columnB, function, getattr(self.jvmCheck, "isLessThan$default$4")()
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isLessThanOrEqualTo(self, columnA, columnB, assertion=is_one):
        """
        Asserts that, in each row, the value of columnA is less than or equal to the value of columnB

        @param columnA Column to run the assertion on
        @param columnB Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.isLessThanOrEqualTo(
            columnA,
            columnB,
            function,
            getattr(self.jvmCheck, "isLessThanOrEqualTo$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isGreaterThan(self, columnA, columnB, assertion=is_one):
        """
        Asserts that, in each row, the value of columnA is greater than the value of columnB

        @param columnA Column to run the assertion on
        @param columnB Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.isGreaterThan(
            columnA,
            columnB,
            function,
            getattr(self.jvmCheck, "isGreaterThan$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isGreaterThanOrEqualTo(self, columnA, columnB, assertion=is_one):
        """
        Asserts that, in each row, the value of columnA is greather than or equal to the value of
        columnB

        @param columnA Column to run the assertion on
        @param columnB Column to run the assertion on
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        jvmConstraint = self.jvmCheck.isGreaterThanOrEqualTo(
            columnA,
            columnB,
            function,
            getattr(self.jvmCheck, "isGreaterThanOrEqualTo$default$4")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isContainedIn(self, column, allowedValues, assertion=is_one):
        """
        Asserts that every non-null value in a column is contained in a set of predefined values

        @param column Column to run the assertion on
        @param allowedValues Allowed values for the column
        @param assertion Function that receives a double input parameter and returns a boolean
        @param hint A hint to provide additional context why a constraint could have failed
        """
        if isinstance(allowedValues, list) == False:
            raise ValueError("'allowedValues' must be a list of strings.")
        function = jc.scala_function1(self.spark.sparkContext._gateway, assertion)
        scalaArray = jc.iterable_to_scala_array(self._jvm, allowedValues)
        jvmConstraint = self.jvmCheck.isContainedIn(
            column,
            scalaArray,
            function,
            getattr(self.jvmCheck, "isContainedIn$default$6")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)

    def isInInterval(
        self,
        column,
        lowerBound,
        upperBound,
        includeLowerBound=True,
        includeUpperBound=True,
    ):
        """
        Asserts that the non-null values in a numeric column fall into the predefined interval

        @param column column to run the assertion
        @param lowerBound lower bound of the interval
        @param upperBound upper bound of the interval
        @param includeLowerBound is a value equal to the lower bound allows?
        @param includeUpperBound is a value equal to the upper bound allowed?
        @param hint A hint to provide additional context why a constraint could have failed
        """
        jvmConstraint = self.jvmCheck.isContainedIn(
            column,
            lowerBound,
            upperBound,
            includeLowerBound,
            includeUpperBound,
            getattr(self.jvmCheck, "isContainedIn$default$6")(),
        )
        return Check(self.spark, self.level, self.description, jvmConstraint)
