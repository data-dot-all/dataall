from datetime import datetime


class StepMetric:
    def __init__(self, name, value, unit=None):
        # self.context = context
        self.name = name
        self.value = value
        self.unit = unit
        self._ts = datetime.now()

    def __str__(self):
        return "type=StepMetric,name={}, value={}, unit={}, ts={}".format(
            self.name, self.value, self.unit, self._ts
        )
