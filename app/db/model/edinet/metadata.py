from dataclasses import dataclass


from db.model.edinet.parameter import Parameter
from db.model.edinet.resultset import Resultset


@dataclass
class Metadata:
    title: str
    parameter: Parameter
    resultset: Resultset
    processDateTime: str  # YYYY-MM-DD hh:mm
    status: str
    message: str

    def __post_init__(self):
        # parameterとresultsetが辞書の場合、dataclassに変換する
        if isinstance(self.parameter, dict):
            self.parameter = Parameter(**self.parameter)
        if isinstance(self.resultset, dict):
            self.resultset = Resultset(**self.resultset)
