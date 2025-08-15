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