from dataclasses import asdict, dataclass
from typing import List

import requests

from db.model.edinet.document_item import Results
from db.model.edinet.metadata import Metadata


# --- Main response dataclass ---


@dataclass
class DocumentListResponseType2:
    metadata: Metadata
    results: List[Results]

    def __post_init__(self):
        # metadataとresultsが辞書または辞書のリストの場合、dataclassに変換する
        if isinstance(self.metadata, dict):
            self.metadata = Metadata(**self.metadata)
        if isinstance(self.results, list):
            self.results = [
                Results(**item) if isinstance(item, dict) else item
                for item in self.results
            ]

    def create_result_items(self):
        yyyymmdd = self.metadata.parameter.date
        # import pdb;pdb.set_trace()

        return [asdict(result.preprocess(yyyymmdd=yyyymmdd)) for result in self.results]


if __name__ == "__main__":

    resp = requests.get(
        "https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2023-08-28&type=2&Subscription-Key=b96412004635453b95a2490d0cfb2e73"
    )

    metadata = DocumentListResponseType2(**resp.json())

    print(metadata)
