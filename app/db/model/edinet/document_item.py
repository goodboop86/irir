from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Results:
    seqNumber: int = None
    docID: str = None
    edinetCode: str = None
    secCode: Optional[str] = None # (*1, *2)
    JCN: Optional[str] = None # (*1)
    filerName: str = None # (*2) - seems to be always present
    fundCode: Optional[str] = None # (*1)
    ordinanceCode: Optional[str] = None # (*1)
    formCode: Optional[str] = None # (*1)
    docTypeCode: Optional[str] = None # (*1)
    periodStart: Optional[str] = None # (*3) - YYYY-MM-DD, optional for some types
    periodEnd: Optional[str] = None # (*3) - YYYY-MM-DD, optional for some types
    submitDateTime: str = None # YYYY-MM-DD hh:mm
    docDescription: str = None
    issuerEdinetCode: Optional[str] = None # (*1, *2)
    subjectEdinetCode: Optional[str] = None # (*1, *2)
    subsidiaryEdinetCode: Optional[str] = None # (*1, *2) - comma-separated if multiple
    currentReportReason: Optional[str] = None # (*4) - comma-separated if multiple
    parentDocID: Optional[str] = None # (*1)
    opeDateTime: str = None # YYYY-MM-DD hh:mm
    withdrawalStatus: str = None
    docInfoEditStatus: str = None
    disclosureStatus: str = None
    xbrlFlag: str = None
    pdfFlag: str = None
    attachDocFlag: str = None
    englishDocFlag: str = None
    csvFlag: str = None
    legalStatus: str = None

    def preprocess(self, yyyymmdd: str):
        if not bool(self.submitDateTime):
            self.submitDateTime = yyyymmdd

        return self


    def submitDateTimeExists(self):
        return bool(self.submitDateTime)
