## type=1
from dataclasses import dataclass

import requests

from backend.main.model.edinet.parameter import Parameter
from backend.main.model.edinet.resultset import Resultset

import json



@dataclass
class Metadata:
    title: str
    parameter: Parameter
    resultset: Resultset
    processDateTime: str  # YYYY-MM-DD hh:mm
    status: str
    message: str