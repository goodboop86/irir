## type=1
from dataclasses import dataclass

import requests



import json

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

    def __init__(self, title: str, parameter: Parameter, resultset: Resultset, processDateTime: str, status: str, message: str):
        self.title = title
        self.parameter = Parameter(**parameter)
        self.resultset = Resultset(**resultset)
        self.processDateTime = processDateTime
        self.status = status
        self.message = message
