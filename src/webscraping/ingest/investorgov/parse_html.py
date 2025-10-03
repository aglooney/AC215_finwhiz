import os
import json
import uuid
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
from datetime import datetime

#config
BASE_URL = "https://www.investor.gov"
ALERTS_URL = BASE_URL + "/news-alerts/investor-alerts-bulletins"
OUTPUT_FILE = "investor_alerts.ndjson"
BUCKET_NAME = os.getenv("GCS_BUCKET")  # set in .env
DESTINATION_BLOB = "scraped/investor_alerts.ndjson"

#ingest builder
def make_record(doc_id: str, url: str, title: str, text: str, chunk_id: int = 0):
    record_id = f"{doc_id}#c{chunk_id}"
    return {
        "id": record_id,
        "source_url": url,
        "title": title,
        "year": None,        # Investor.gov alerts don't map cleanly here
        "section": None,
        "authority": "investor.gov",
        "doctype": "alert",
        "language": "en",
        "text": text,
        "page": None
    }

#scraper
def scrape_investor_alerts():
    response = requests.get(ALERTS_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    articles = soup.select("div.views-row")
    for article in articles:
        title_tag = article.select_one("h3 a")
        date_tag = article.select_one("span.date-display-single")

        title = title_tag.get_text(strip=True) if title_tag else "Untitled"
        url = BASE_URL + title_tag["href"] if title_tag else BASE_URL
        date = date_tag.get_text(strip=True) if date_tag else ""

        # Use UUID for doc_id to avoid collisions
        doc_id = str(uuid.uuid4())
        text = f"{title} ({date})"  # minimal text, could scrape article body instead

        yield make_record(doc_id, url, title, text)

#write ndjson
def write_ndjson(records, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

#gcs_upload
def upload_to_gcs(bucket_name, source_file, destination_blob):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"Uploaded {source_file} to gs://{bucket_name}/{destination_blob}")


if __name__ == "__main__":
    records = list(scrape_investor_alerts())
    write_ndjson(records, OUTPUT_FILE)
    upload_to_gcs(BUCKET_NAME, OUTPUT_FILE, DESTINATION_BLOB)
