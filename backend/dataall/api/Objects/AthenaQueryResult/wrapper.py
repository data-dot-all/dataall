from enum import Enum
from typing import List


class AthenaQueryResultStatus(Enum):
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"


class AthenaQueryResult:
    props = [
        "Status",
        "Error",
        "AthenaQueryId",
        "ElapsedTimeInMs",
        "DataScannedInBytes",
        "OutputLocation",
        "rows",
        "columns",
    ]

    def __init__(
        self,
        Error: str = None,
        Status: str = None,
        AthenaQueryId: str = None,
        ElapsedTimeInMs: int = None,
        DataScannedInBytes: int = None,
        OutputLocation: str = None,
        rows: List = None,
        columns: List = None,
        **kwargs,
    ):
        self._error = Error
        self._status = Status
        self._query_id = AthenaQueryId
        self._elapsed_time = ElapsedTimeInMs
        self._data_scanned = DataScannedInBytes
        self._loc = OutputLocation
        self._rows = rows
        self._columns = columns

    def to_dict(self):
        return {k: getattr(self, k) for k in AthenaQueryResult.props}

    @property
    def Status(self) -> AthenaQueryResultStatus:
        return self._status

    @property
    def Error(self) -> str:
        return self._error

    @property
    def AthenaQueryId(self):
        return self._query_id

    @property
    def ElapsedTimeInMs(self):
        return self._elapsed_time

    @property
    def DataScannedInBytes(self):
        return self._data_scanned

    @property
    def OutputLocation(self):
        return self._loc

    @property
    def rows(self):
        return self._rows

    @property
    def columns(self):
        return self._columns
