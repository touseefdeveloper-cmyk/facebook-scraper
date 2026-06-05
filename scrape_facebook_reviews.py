import requests
import json
import time
import os
import re

API_KEY = os.environ.get("WEBSCRAPING_AI_KEY_FB", "")
TEXT_URL = "https://api.webscraping.ai/text"

BUSINESSES = [
    {"id": "cabinet-refresh",          "facebook_url": "https://www.facebook.com/CabinetRefresh/"},
    {"id": "american-vision-windows",  "facebook_url": "https://www.facebook.com/AmericanVisionWindows/"},
    {"id": "one-week-bath",            "facebook_url": "https://www.facebook.com/oneweekbath/"},
    {"id": "abc-pro",                  "facebook_url": "https://www.facebook.com/TheABCPro/"},
    {"id": "1-degree-construction",    "facebook_url": "https://www.facebook.com/1degreeconstruction"},
    {"id": "mr-cabinet-care",          "facebook_url": "https://www.facebook.com/Cabinet.Care"},
    {"id": "payless-kitchen-cabinets", "facebook_url": "https://www.facebook.com/paylesskitchencabinets/"},
    {"id": "payless-bath-makeover",    "facebook_url": "https://www.facebook.com/PaylessBathMakeover/"},
    {"id": "adar-builders",            "facebook_url": "https://www.facebook.com/adarbuilders/"},
    {"id": "gm-home-remodeling",       "facebook_url": "https://www.facebook.com/GandMHomeRemodelinginc/"},
]

RETRY_DELAY = 30


def parse_reviews_from_text(text: str) -> dict:
    """
    Facebook uses: "96% recommend (496 Reviews)"
    or:            "Not yet rated (0 Reviews)"
    """
    total_reviews = None
    recommend_percent = None

    m = re.search(r'\((\d+)\s+Reviews?\)', text, re.IGNORECASE)
    if m:
        total_reviews = m.group(1)

    m = re.search(r'(\d+)%\s+recommend', text, re.IGNORECASE)
    if m:
        recommend_percent = m.group(1)

    return {"total_reviews": total_reviews, "recommend_percent": recommend_percent}


def fetch_text(url: str, proxy: str) -> str:
    params = {
        "api_key": API_KEY,
        "url": url,
        "js": "true",
        "proxy": proxy,
        "timeout": 30000,
        "country": "us",
        "wait_for": "h1",
    }
    response = requests.get(TEXT_URL, params=params, timeout=90)
    response.raise_for_status()
    return response.text


def scrape_facebook(business: dict) -> dict:
    print(f"  [{business['id']}] Scraping ...")

    proxy_attempts = [("residential", 2), ("stealth", 2)]
    last_error = None

    for proxy, tries in proxy_attempts:
        for attempt in range(1, tries + 1):
            try:
                print(f"    [{proxy}] Attempt {attempt}/{tries} ...")
                text = fetch_text(business["facebook_url"], proxy)
                parsed = parse_reviews_from_text(text)

                if parsed["total_reviews"] is None:
                    snippet = " ".join(text.split())[:400]
                    print(f"    ⚠ Could not parse data. Snippet: {snippet}")

                result = {
                    "id": business["id"],
                    "facebook_url": business["facebook_url"],
                    "total_reviews": parsed["total_reviews"],
                    "recommend_percent": parsed["recommend_percent"],
                    "error": None,
                }
                print(f"    ✓ Reviews: {result['total_reviews']} | Recommend: {result['recommend_percent']}%")
                return result

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                print(f"    ✗ [{proxy}] Attempt {attempt} failed: {e}")
                if attempt < tries:
                    print(f"    Retrying in {RETRY_DELAY}s ...")
                    time.sleep(RETRY_DELAY)

        print(f"    Switching to next proxy type ...")
        time.sleep(RETRY_DELAY)

    print(f"    ✗ All proxy attempts exhausted.")
    return {"id": business["id"], "facebook_url": business["facebook_url"], "total_reviews": None, "recommend_percent": None, "error": last_error}


def main():
    print("=== Facebook Review Scraper ===\n")
    results = []

    for business in BUSINESSES:
        result = scrape_facebook(business)
        results.append(result)
        time.sleep(15)

    output_file = "facebook_reviews.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n=== Done! Results saved to {output_file} ===")


if __name__ == "__main__":
    main()
