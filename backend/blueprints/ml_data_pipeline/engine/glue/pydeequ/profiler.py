class ColumnProfilerRunBuilder:
    """
    Builds profiling runner.
    """

    def __init__(self, dataFrame):
        """
        Args:
            dataFrame (pyspark.sql.dataframe.DataFrame):
        """
        self._sc = dataFrame._sc
        self._dataFrame = dataFrame
        run_builder = self._jvm.com.amazon.deequ.profiles.ColumnProfilerRunBuilder
        self.jvmColumnProfilerRunBuilder = run_builder(self._dataFrame._jdf)

    @property
    def _jvm(self):
        return self._sc._jvm

    @property
    def dataFrame(self):
        return self._dataFrame

    def run(self):
        result = self.jvmColumnProfilerRunBuilder.run()

        seqColumnProfiles = result.profiles().values().toSeq()
        jf = result.toJson(seqColumnProfiles)

        return jf


class ColumnProfilerRunner:
    """
    Responsible for running data profiling.
    """

    def onData(self, dataFrame):
        """
        Starting point to construct a profiling runner.

        Args:
            dataFrame (pyspark.sql.dataframe.DataFrame):
        """
        return ColumnProfilerRunBuilder(dataFrame)
