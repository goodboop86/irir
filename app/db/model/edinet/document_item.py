from dataclasses import dataclass
import logging
from pprint import pprint
from typing import Optional

from common.main.lib.utils import Utils
from db.model.edinet.edinet_enums import DisclosureStatus, RegalStatus


@dataclass
class Results:
    JCN: Optional[str] = None  # (*1)
    currentReportReason: Optional[str] = None  # (*4) - comma-separated if multiple
    disclosureStatus: str = None
    docID: str = None
    docInfoEditStatus: str = None
    docTypeCode: Optional[str] = None  # (*1)
    docDescription: str = None
    edinetCode: str = None
    fundCode: Optional[str] = None  # (*1)
    filerName: str = None  # (*2) - seems to be always present
    formCode: Optional[str] = None  # (*1)
    issuerEdinetCode: Optional[str] = None  # (*1, *2)
    legalStatus: str = None
    ordinanceCode: Optional[str] = None  # (*1)
    opeDateTime: str = None  # YYYY-MM-DD hh:mm
    periodStart: Optional[str] = None  # (*3) - YYYY-MM-DD, optional for some types
    periodEnd: Optional[str] = None  # (*3) - YYYY-MM-DD, optional for some types
    parentDocID: Optional[str] = None  # (*1)
    seqNumber: int = None
    secCode: Optional[str] = None  # (*1, *2)
    submitDateTime: str = None  # YYYY-MM-DD hh:mm
    subjectEdinetCode: Optional[str] = None  # (*1, *2)
    subsidiaryEdinetCode: Optional[str] = None  # (*1, *2) - comma-separated if multiple
    withdrawalStatus: str = None
    attachDocFlag: str = None
    csvFlag: str = None
    englishDocFlag: str = None
    pdfFlag: str = None
    xbrlFlag: str = None
    logger = logging.getLogger(__name__)


    def has_submitdatetime(self):
        return bool(self.submitDateTime)

    def has_edinetcode(self):
        return bool(self.edinetCode)

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

    def is_viewable(self) -> RegalStatus:
        status = RegalStatus.from_string(self.legalStatus)
        is_viewable = status in [RegalStatus.ON_VIEW or RegalStatus.EXTENDED]
        if not is_viewable:
            self.logger.info(f"[SKIP] {self.docID} is not viewable.")
        return is_viewable
    
    def has_anyitem(self) -> RegalStatus:
        has_anyitem = any([self.has_pdf(), self.has_csv(), self.has_xbrl(), self.has_attachdoc(), self.has_englishdoc()])
        if not has_anyitem:
            self.logger.info(f"[SKIP] {self.docID} does'nt have enough information.")
        return has_anyitem
    
    def has_edinetcode(self) -> RegalStatus:
        has_edinetcode = self.has_edinetcode()
        if not has_edinetcode:
            self.logger.info(f"[SKIP] {self.docID} does'nt have edinet-code.")
        return has_edinetcode
    
    def get_disclosurestatus(self) -> DisclosureStatus:
        return DisclosureStatus.from_string(self.legalStatus)

    def preprocess(self, yyyymmdd: str):
        """DynamoDB登録用に整形して返す"""
        self.__embed_date_if_not_exist(yyyymmdd=yyyymmdd)
        self.__embed_edinetcode_if_not_exist()
        return self

    def __embed_date_if_not_exist(self, yyyymmdd: str):
        """submitDateTimeが存在しないなら、受け取った日付(APIリクエスト日を想定)を埋めて返す"""
        if not bool(self.submitDateTime):
            self.submitDateTime = yyyymmdd

    def __embed_edinetcode_if_not_exist(self, text: str = "NOT_SPECIFIED"):
        """submitDateTimeが存在しないなら、受け取った日付(APIリクエスト日を想定)を埋めて返す"""
        if not bool(self.edinetCode):
            self.edinetCode = text
