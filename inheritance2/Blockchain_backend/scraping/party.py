from playwright.sync_api import sync_playwright
from pymongo import MongoClient
from datetime import datetime

# --- MongoDB Atlas Configuration ---
MONGO_URI = "mongodb+srv://manaswirane1947_db_user:tiBNMut48iy2HVDi@cluster0.82qkus1.mongodb.net/eci?retryWrites=true&w=majority"

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client.get_database()  # Automatically uses the database in the URI
collection = db["political_parties"]

# --- Target URL ---
URL = "https://www.eci.gov.in/constitution-of-political-party"

# --- Playwright Scraper ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=200)
    try:
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        # Wait for the list of parties to load
        page.wait_for_selector("ul.political-party-registration li", timeout=60000)
        items = page.query_selector_all("ul.political-party-registration li")
        print("Total LI items found:", len(items))

        count = 0
        for li in items:
            # Party name (always in h4)
            h4 = li.query_selector("h4")
            if not h4:
                continue

            party_name = h4.inner_text().strip()
            if not party_name:
                continue

            # Optional PDF link
            a = li.query_selector('a.lofb[href]')
            pdf_link = a.get_attribute("href") if a else None

            print(party_name, "->", pdf_link)

            # Upsert into MongoDB
            collection.update_one(
                {"party_name": party_name},
                {
                    "$set": {
                        "party_name": party_name,
                        "pdf_link": pdf_link,
                        "source": "eci.gov.in",
                        "fetched_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

            count += 1

    finally:
        browser.close()

print(f"Inserted/updated {count} parties in MongoDB Atlas.")
