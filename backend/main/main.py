import requests
import os
from app.backend.model.edinet_response_parser import parse_edinet_response, EdinetDocumentListResponse

# Get API key from environment variable
# Ensure you have a .env file in the project root with EDINET_API_KEY=your_api_key_here
# or set the environment variable directly.
EDINET_API_KEY = os.environ.get("EDINET_API_KEY")
EDINET_BASE_URL = "https://api.edinet-fsa.go.jp/api/v2/documents.json"

def fetch_edinet_documents(date: str, doc_type: str = "2") -> Optional[EdinetDocumentListResponse]:
    """
    Fetches documents from the EDINET API for a given date and document type.

    Args:
        date: The date to fetch documents for (YYYY-MM-DD).
        doc_type: The type of document to fetch (e.g., "1" for metadata only, "2" for full list).

    Returns:
        A parsed EdinetDocumentListResponse object if successful, None otherwise.
    """
    if not EDINET_API_KEY:
        print("Error: EDINET_API_KEY environment variable not set.")
        print("Please create a .env file with EDINET_API_KEY=your_api_key_here or set the environment variable.")
        return None

    params = {
        "date": date,
        "type": doc_type,
        "Subscription-Key": EDINET_API_KEY
    }

    try:
        response = requests.get(EDINET_BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        # The API might return an error structure even with a 200 status code if the request itself was valid but data retrieval failed.
        # We rely on our parser to handle the structure.
        parsed_response = parse_edinet_response(data)
        return parsed_response

    except requests.exceptions.RequestException as e:
        print(f"Error fetching EDINET documents: {e}")
        return None
    except Exception as e:
        print(f"Error parsing EDINET response: {e}")
        return None

if __name__ == '__main__':
    # Example usage:
    # Fetch documents for a specific date
    target_date = "2023-08-28"
    print(f"Fetching EDINET documents for {target_date}...")
    
    documents_response = fetch_edinet_documents(target_date)

    if documents_response:
        print(f"\nSuccessfully fetched and parsed {documents_response.metadata.resultset.count} documents.")
        print(f"API Status: {documents_response.metadata.status} - {documents_response.metadata.message}")
        print(f"Last updated: {documents_response.metadata.processDateTime}")

        # Display details of the first few documents
        print("\n--- First 3 Documents ---")
        for i, doc in enumerate(documents_response.results[:3]):
            print(f"\nDocument {i+1}:")
            print(f"  Doc ID: {doc.docID}")
            print(f"  Filer Name: {doc.filerName}")
            print(f"  Document Type: {doc.docDescription}")
            print(f"  Submit Date: {doc.submitDateTime}")
            print(f"  PDF Available: {'Yes' if doc.pdfFlag == '1' else 'No'}")
    else:
        print("Failed to fetch or parse EDINET documents.")
