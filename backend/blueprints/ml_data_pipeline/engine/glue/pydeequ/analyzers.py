import engine.glue.pydeequ.jvm_conversions as jc


class BaseAnalyzer(object):
    """
    Analyzer baseclass
    """

    def set_jvm(self, jvm):
        self._jvm = jvm
        return self

    @property
    def jvmdeequAnalyzers(self):
        if self._jvm:
            return self._jvm.com.amazon.deequ.analyzers
        else:
            raise ValueError("Run set_jvm() method first.")


class ApproxCountDistinct(BaseAnalyzer):
    """
    Compute approximated count distinct with HyperLogLogPlusPlus.

    @param column Which column to compute this aggregation on.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.ApproxCountDistinct(
            self.column,
            getattr(self.jvmdeequAnalyzers.ApproxCountDistinct, "apply$default$2")(),
        )


class ApproxQuantile(BaseAnalyzer):
    """
    Approximate quantile analyzer. The allowed relative error compared to the exact quantile can be
    configured with `relativeError` parameter. A `relativeError` = 0.0 would yield the exact
    quantile while increasing the computational load.

    @param column Column in DataFrame for which the approximate quantile is analyzed.
    @param quantile Computed Quantile. Must be in the interval [0, 1], where 0.5 would be the
                    median.
    @param relativeError Relative target precision to achieve in the quantile computation.
                         Must be in the interval [0, 1].
    @param where Additional filter to apply before the analyzer is run.
    """

    def __init__(self, column, quantile, relativeError=0.01):
        self.column = column
        self.quantile = quantile
        self.relativeError = relativeError

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.ApproxQuantile(
            self.column,
            self.quantile,
            self.relativeError,
            getattr(self.jvmdeequAnalyzers.ApproxQuantile, "apply$default$4")(),
        )


class Completeness(BaseAnalyzer):
    """
    Fraction of non-null values in a column.

    Args:
        column Column in DataFrame
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Completeness(
            self.column,
            getattr(self.jvmdeequAnalyzers.Completeness, "apply$default$2")(),
        )


class Compliance(BaseAnalyzer):
    """
    Compliance is a measure of the fraction of rows that complies with the given column constraint.
    E.g if the constraint is "att1>3" and data frame has 5 rows with att1 column value greater than
    3 and 10 rows under 3; a DoubleMetric would be returned with 0.33 value
        @param instance         Unlike other column analyzers (e.g completeness) this analyzer can not
                            infer to the metric instance name from column name.
                            Also the constraint given here can be referring to multiple columns,
                            so metric instance name should be provided,
                            describing what the analysis being done for.
    @param predicate SQL-predicate to apply per row
    @param where Additional filter to apply before the analyzer is run.
    """

    def __init__(self, instance, predicate):
        self.instance = instance
        self.predicate = predicate

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Compliance(
            self.instance,
            self.predicate,
            getattr(self.jvmdeequAnalyzers.Compliance, "apply$default$3")(),
        )


class Correlation(BaseAnalyzer):
    """
    Computes the pearson correlation coefficient between the two given columns
        @param firstColumn First input column for computation
    @param secondColumn Second input column for computation
    """

    def __init__(self, firstColumn, secondColumn):
        self.firstColumn = firstColumn
        self.secondColumn = secondColumn

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Correlation(
            self.firstColumn,
            self.secondColumn,
            getattr(self.jvmdeequAnalyzers.Correlation, "apply$default$3")(),
        )


class CountDistinct(BaseAnalyzer):
    """
    Number of distinct values
    """

    def __init__(self, column):
        if isinstance(column, str):
            self.column = [column]
        elif isinstance(column, list):
            self.column = column
        else:
            raise ValueError("'column' must be string or list of strings.")

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.CountDistinct(
            jc.iterable_to_scala_seq(self._jvm, self.column)
        )


class DataType(BaseAnalyzer):
    """
    Distribution of data types such as Boolean, Fractional, Integral, and String.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.DataType(
            self.column, getattr(self.jvmdeequAnalyzers.DataType, "apply$default$2")()
        )


class Distinctness(BaseAnalyzer):
    """
    Distinctness is the fraction of distinct values of a column(s).
        @param columns  the column(s) for which to compute distinctness
    """

    def __init__(self, columns):
        if isinstance(columns, str):
            self.columns = [columns]
        elif isinstance(columns, list):
            self.columns = columns
        else:
            raise ValueError("'columns' must be string or list of strings.")

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Distinctness(
            jc.iterable_to_scala_seq(self._jvm, self.columns),
            getattr(self.jvmdeequAnalyzers.DataType, "apply$default$2")(),
        )


class Entropy(BaseAnalyzer):
    """
    Entropy is a measure of the level of information contained in a message. Given the probability
    distribution over values in a column, it describes how many bits are required to identify a
    value.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Entropy(
            self.column, getattr(self.jvmdeequAnalyzers.Entropy, "apply$default$2")()
        )


class Histogram(BaseAnalyzer):
    """
    Histogram is the summary of values in a column of a DataFrame. Groups the given column's values,
    and calculates the number of rows with that specific value and the fraction of this value.

    @param column        Column to do histogram analysis on
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Histogram(
            self.column,
            getattr(self.jvmdeequAnalyzers.Histogram, "apply$default$2")(),
            getattr(self.jvmdeequAnalyzers.Histogram, "apply$default$3")(),
            getattr(self.jvmdeequAnalyzers.Histogram, "apply$default$4")(),
        )


class Maximum(BaseAnalyzer):
    """
    Maximum value.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Maximum(
            self.column, getattr(self.jvmdeequAnalyzers.Maximum, "apply$default$2")()
        )


class MaxLength(BaseAnalyzer):
    """"""

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.MaxLength(
            self.column, getattr(self.jvmdeequAnalyzers.MaxLength, "apply$default$2")()
        )


class Mean(BaseAnalyzer):
    """
    Mean value, null values are excluded.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Mean(
            self.column, getattr(self.jvmdeequAnalyzers.Mean, "apply$default$2")()
        )


class Minimum(BaseAnalyzer):
    """
    Minimum value.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Minimum(
            self.column, getattr(self.jvmdeequAnalyzers.Minimum, "apply$default$2")()
        )


class MinLength(BaseAnalyzer):
    """"""

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.MinLength(
            self.column, getattr(self.jvmdeequAnalyzers.MinLength, "apply$default$2")()
        )


class MutualInformation(BaseAnalyzer):
    """
    Mutual Information describes how much information about one column can be inferred from another
    column.

    If two columns are independent of each other, then nothing can be inferred from one column about
    the other, and mutual information is zero. If there is a functional dependency of one column to
    another and vice versa, then all information of the two columns are shared, and mutual
    information is the entropy of each column.
    """

    def __init__(self, columns):
        if not isinstance(columns, list):
            raise ValueError("'columns' mus be a list of strings.")
        self.columns = columns

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.MutualInformation(
            jc.iterable_to_scala_seq(self._jvm, self.columns),
            getattr(self.jvmdeequAnalyzers.MutualInformation, "apply$default$2")(),
        )


# class PattenMatch


class Size(BaseAnalyzer):
    """
    Size is the number of rows in a DataFrame.
    """

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Size(
            getattr(self.jvmdeequAnalyzers.Size, "apply$default$1")()
        )


class StandardDeviation(BaseAnalyzer):
    """
    Standard deviation implementation.
    """

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.StandardDeviation(
            self.column,
            getattr(self.jvmdeequAnalyzers.StandardDeviation, "apply$default$2")(),
        )


class Sum(BaseAnalyzer):
    """"""

    def __init__(self, column):
        self.column = column

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Sum(
            self.column, getattr(self.jvmdeequAnalyzers.Sum, "apply$default$2")()
        )


class Uniqueness(BaseAnalyzer):
    """
    Fraction of unique values over the number of all values of
    a column. Unique values occur exactly once.
    Example: [a, a, b] contains one unique value b,
    so uniqueness is 1/3.
    """

    def __init__(self, columns):
        if not isinstance(columns, list):
            raise ValueError("'columns' mus be a list of strings.")
        self.columns = columns

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.Uniqueness(
            jc.iterable_to_scala_seq(self._jvm, self.columns),
            getattr(self.jvmdeequAnalyzers.Uniqueness, "apply$default$2")(),
        )


class UniqueValueRatio(BaseAnalyzer):
    """
    Fraction of unique values over the number of all distinct
    values of a column. Unique values occur exactly once.
    Distinct values occur at least once.
    Example: [a, a, b] contains one unique value b,
    and two distinct values a and b, so the unique value
    ratio is 1/2.
    """

    def __init__(self, columns):
        if not isinstance(columns, list):
            raise ValueError("'columns' mus be a list of strings.")
        self.columns = columns

    @property
    def jvmAnalyzer(self):
        return self.jvmdeequAnalyzers.UniqueValueRatio(
            jc.iterable_to_scala_seq(self._jvm, self.columns),
            getattr(self.jvmdeequAnalyzers.UniqueValueRatio, "apply$default$2")(),
        )
