from dataclasses import dataclass
from typing import Optional

from common.main.lib.utils import Utils
from db.model.edinet.edinet_enums import DisclosureStatus, RegalStatus


@dataclass
class Results:
    seqNumber: int = None
    docID: str = None
    edinetCode: str = None
    secCode: Optional[str] = None  # (*1, *2)
    JCN: Optional[str] = None  # (*1)
    filerName: str = None  # (*2) - seems to be always present
    fundCode: Optional[str] = None  # (*1)
    ordinanceCode: Optional[str] = None  # (*1)
    formCode: Optional[str] = None  # (*1)
    docTypeCode: Optional[str] = None  # (*1)
    periodStart: Optional[str] = None  # (*3) - YYYY-MM-DD, optional for some types
    periodEnd: Optional[str] = None  # (*3) - YYYY-MM-DD, optional for some types
    submitDateTime: str = None  # YYYY-MM-DD hh:mm
    docDescription: str = None
    issuerEdinetCode: Optional[str] = None  # (*1, *2)
    subjectEdinetCode: Optional[str] = None  # (*1, *2)
    subsidiaryEdinetCode: Optional[str] = None  # (*1, *2) - comma-separated if multiple
    currentReportReason: Optional[str] = None  # (*4) - comma-separated if multiple
    parentDocID: Optional[str] = None  # (*1)
    opeDateTime: str = None  # YYYY-MM-DD hh:mm
    withdrawalStatus: str = None
    docInfoEditStatus: str = None
    disclosureStatus: str = None
    xbrlFlag: str = None
    pdfFlag: str = None
    attachDocFlag: str = None
    englishDocFlag: str = None
    csvFlag: str = None
    legalStatus: str = None

    def has_submitdatetime(self):
        return bool(self.submitDateTime)

    def has_pdf(self) -> bool:
        return Utils.broad_enable(self.pdfFlag)

    def has_csv(self) -> bool:
        return Utils.broad_enable(self.csvFlag)

    def has_xbrl(self) -> bool:
        return Utils.broad_enable(self.xbrlFlag)

    def has_attachdoc(self) -> bool:
        return Utils.broad_enable(self.attachDocFlag)

    def has_englishdoc(self) -> bool:
        return Utils.broad_enable(self.englishDocFlag)

    def get_regalstatus(self) -> RegalStatus:
        return RegalStatus.from_string(self.legalStatus)

    def get_disclosurestatus(self) -> RegalStatus:
        return DisclosureStatus.from_string(self.legalStatus)

    def preprocess(self, yyyymmdd: str):
        """DynamoDB登録用に整形して返す"""
        self.__embed_date_if_not_exist(yyyymmdd=yyyymmdd)

        return self

    def __embed_date_if_not_exist(self, yyyymmdd: str):
        """submitDateTimeが存在しないなら、受け取った日付(APIリクエスト日を想定)を埋めて返す"""
        if not bool(self.submitDateTime):
            self.submitDateTime = yyyymmdd
