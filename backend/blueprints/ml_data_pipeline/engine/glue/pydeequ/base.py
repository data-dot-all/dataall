class BaseBuilder(object):
    def __init__(self, SparkSession, dataFrame):
        self.spark = SparkSession
        self._dataFrame = dataFrame

    @property
    def _jsparkSession(self):
        return self.spark._jsparkSession

    @property
    def _jvm(self):
        return self.spark.sparkContext._jvm

    @property
    def dataFrame(self):
        return self._dataFrame


class VerificationRunBuilder(BaseBuilder):
    """
    A class to build a VerificationRun using a fluent API.
    """

    def __init__(self, SparkSession, dataFrame):
        """
        Args:
            SparkSession (pyspark.sql.SparkSession)
            dataFrame (pyspark.sql.dataframe.DataFrame)
        """
        super().__init__(SparkSession, dataFrame)
        run_builder = self._jvm.com.amazon.deequ.VerificationRunBuilder
        self.jvmVerificationRunBuilder = run_builder(self.dataFrame._jdf)

    def addCheck(self, check):
        """
        Add a single check to the run.

        Args:
            check (pydeequ.check.Check):
            A check object to be executed during the run
        """
        jvmCheck = check.jvmCheck
        self.jvmVerificationRunBuilder.addCheck(jvmCheck)
        return self

    def run(self):
        result = self.jvmVerificationRunBuilder.run()

        jvmVerificationResult = self._jvm.com.amazon.deequ.VerificationResult
        try:
            df = jvmVerificationResult.checkResultsAsDataFrame(
                self._jsparkSession,
                result,
                getattr(jvmVerificationResult, "checkResultsAsDataFrame$default$3")(),
            )
            return df
        except Exception:
            self.spark.sparkContext._gateway.close()
            self.spark.stop()
            raise AttributeError


class VerificationSuite:
    """
    Responsible for running checks and required analysis and return the
    results.
    """

    def __init__(self, SparkSession):
        """
        Args:
            SparkSession ():
        """
        self.spark = SparkSession
        self._start_callback_server()

    @property
    def _gateway(self):
        return self.spark.sparkContext._gateway

    def _start_callback_server(self):
        callback = self._gateway.get_callback_server()
        if callback is None:
            self._gateway.start_callback_server()
        elif callback.is_shutdown:
            callback.close()
            self._gateway.restart_callback_server()

    def onData(self, dataFrame):
        """
        Starting point to construct a VerificationRun.

        Args:
            dataFrame (pyspark.sql.dataframe.DataFrame):
            spark dataFrame on which the checks will be verified.
        """
        return VerificationRunBuilder(self.spark, dataFrame)


class AnalysisRunBuilder(BaseBuilder):
    """
    A class to build an AnalysisRun using a fluent API.
    """

    def __init__(self, SparkSession, dataFrame):
        """
        Args:
            SparkSession (pyspark.sql.SparkSession)
            dataFrame (pyspark.sql.dataframe.DataFrame)
        """
        super().__init__(SparkSession, dataFrame)
        run_builder = self._jvm.com.amazon.deequ.analyzers.runners.AnalysisRunBuilder
        self.jvmAnalysisRunBuilder = run_builder(self.dataFrame._jdf)

    def addAnalyzer(self, analyzer):
        """
        Add a single analyzer to the run.

        Args:
            analyzer (pydeequ.analyzer.Analyzer):
            An analyzer object to be executed during the run
        """
        analyzer.set_jvm(self._jvm)
        jvmAnalyzer = analyzer.jvmAnalyzer
        self.jvmAnalysisRunBuilder.addAnalyzer(jvmAnalyzer)
        return self

    def run(self):
        result = self.jvmAnalysisRunBuilder.run()

        jvmAnalyzerContext = (
            self._jvm.com.amazon.deequ.analyzers.runners.AnalyzerContext
        )
        try:
            df = jvmAnalyzerContext.successMetricsAsDataFrame(
                self._jsparkSession,
                result,
                getattr(jvmAnalyzerContext, "successMetricsAsDataFrame$default$3")(),
            )
            return df
        except Exception:
            self.spark.sparkContext._gateway.close()
            self.spark.stop()
            raise AttributeError


class AnalysisRunner:
    """
    Responsible for running metrics calculations.
    """

    def __init__(self, SparkSession):
        """
        Args:
            SparkSession ():
        """
        self.spark = SparkSession

    def onData(self, dataFrame):
        """
        Starting point to construct an Analysisrun.

        Args:
            dataFrame (pyspark.sql.dataframe.DataFrame):
            spark dataFrame on which the checks will be verified.
        """
        return AnalysisRunBuilder(self.spark, dataFrame)


class ConstraintSuggestionRunBuilder(BaseBuilder):
    """
    A class to build a ConstraintSuggestionRun using a fluent API.
    """

    def __init__(self, SparkSession, dataFrame):
        """
        Args:
            SparkSession (pyspark.sql.SparkSession)
            dataFrame (pyspark.sql.dataframe.DataFrame)
        """
        super().__init__(SparkSession, dataFrame)
        run_builder = (
            self._jvm.com.amazon.deequ.suggestions.ConstraintSuggestionRunBuilder
        )
        self.jvmConstraintSuggestionRunBuilder = run_builder(self.dataFrame._jdf)

    def addConstraintRule(self, constraint):
        """
        Add a single rule for suggesting constraints based on ColumnProfiles to the run.

        Args:
            constraintRule
        """
        jvmRule = constraint._jvmRule
        self.jvmConstraintSuggestionRunBuilder.addConstraintRule(jvmRule())
        return self

    def run(self):
        result = self.jvmConstraintSuggestionRunBuilder.run()

        jvmSuggestionResult = (
            self._jvm.com.amazon.deequ.suggestions.ConstraintSuggestionResult
        )
        try:
            df = jvmSuggestionResult.getConstraintSuggestionsAsJson(result)
            return df
        except:
            self.spark.sparkContext._gateway.close()
            self.spark.stop()
            raise AttributeError


class ConstraintSuggestionRunner:
    """"""

    def __init__(self, SparkSession):
        """
        Args:
            SparkSession ():
        """
        self.spark = SparkSession

    def onData(self, dataFrame):
        """
        Starting point to construct a run on constraint suggestions.

        Args:
            dataFrame (pyspark.sql.dataframe.DataFrame):
            spark dataFrame on which the checks will be verified.
        """
        return ConstraintSuggestionRunBuilder(self.spark, dataFrame)
