from dataclasses import dataclass

import requests

from db.main.model.edinet.metadata import Metadata


# --- Main response dataclass ---


@dataclass
class DocumentListResponseType1:
    metadata: Metadata


if __name__ == "__main__":
    resp = requests.get(
        "https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2023-08-28&type=1&Subscription-Key=b96412004635453b95a2490d0cfb2e73"
    )

    metadata = DocumentListResponseType1(resp.json())

    print(metadata)
