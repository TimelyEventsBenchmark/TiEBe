
import os
import sys
import time
import random
import json
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import numpy as np

def massiveweb_filter_all_rules(
    text,
    min_words=50,
    max_words=100_000,
    min_word_chars=3,
    max_word_chars=10,
    max_symbol_to_word_ratio=0.1,
    max_lines_end_ellipsis_pct=0.3,
    min_words_alphabetic_char_pct=0.9,
):
    failed_rules = []

    words = " ".join(text.split()).split()
    num_words = len(words)

    if num_words < min_words or num_words > max_words:
        failed_rules.append("rule1_minmax_words")

    num_symbols = sum([word == "#" or word == "..." for word in words])
    if num_words > 0:
        if (num_symbols / max(1, (num_words - num_symbols))) > max_symbol_to_word_ratio:
            failed_rules.append("rule3_symbol_word_ratio")

    if num_words > 0:
        alpha_ratio = np.mean([any(char.isalpha() for char in word) for word in words])
        if alpha_ratio < min_words_alphabetic_char_pct:
            failed_rules.append("rule5_words_alphabetic_char_pct")
    else:
        failed_rules.append("rule5_words_alphabetic_char_pct")

    return failed_rules


def extract_only_paragraphs(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return " ".join(paragraphs)


def massiveweb_filter_wrapper(text_clean):
    failed_rules = massiveweb_filter_all_rules(text_clean)

    if failed_rules:
        return None
    else:
        return text_clean


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
     Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)\
     Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
     Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X)\
     AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 \
     (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36'
]

additional_headers = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.reuters.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,\
               image/avif,image/webp,image/apng,*/*;q=0.8,\
               application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Upgrade-Insecure-Requests': '1'
}

def fetch_with_retry(url, retries=3, delay=2):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    headers = {"User-Agent": random.choice(user_agents)}
    headers.update(additional_headers)

    try:
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        time.sleep(delay + random.uniform(0, 1))
        return response.text
    except requests.RequestException as e:
        print(f"Failed to access {url} via Requests: {e}")
        return None

def fetch_with_playwright(url, delay=2):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=random.choice(user_agents),
                extra_http_headers=additional_headers
            )
            page.goto(url, timeout=60000)
            time.sleep(delay + random.uniform(0, 1))
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"Playwright failed to access {url}: {e}")
        return None

def extract_main_article_text(soup):
    article_tag = soup.find("article")
    if article_tag:
        return article_tag.get_text(separator=" ", strip=True)

    main_tag = soup.find("main")
    if main_tag:
        return main_tag.get_text(separator=" ", strip=True)

    div_tags = soup.find_all(["div", "section"])
    best_text = ""
    for tag in div_tags:
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > len(best_text):
            best_text = text

    if best_text:
        return best_text

    body = soup.find("body")
    if body:
        return body.get_text(separator=" ", strip=True)

    return ""

def extract_with_beautifulsoup(html):
    page_title = ""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title:
        if soup.title.string:
            page_title = soup.title.string.strip()
    else:
        page_title = soup.title or ""
    main_text = extract_main_article_text(soup)

    return {
        "page_title": page_title if page_title else "",
        "main_text": main_text,
    }

def read_json(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)

def load_existing_extractions(output_filename):
    if not os.path.exists(output_filename):
        return set(), []

    with open(output_filename, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return set(), []

    existing_links = set()
    for ev in data:
        for link_data in ev.get("links", []):
            existing_links.add(link_data.get("link", ""))

    return existing_links, data

def scrape_events(events_json, year, country):
    final_text = ""
    final_title = ""
    output_filename = f"{country}/extracted_events_{year}_{country}.json"
    existing_links, extracted_events = load_existing_extractions(output_filename)

    existing_events_map = {}
    for idx, ev in enumerate(extracted_events):
        key = (
            ev.get("event_text", ""),
            ev.get("start_date", ""),
            ev.get("end_date", "")
        )
        existing_events_map[key] = idx

    for event in events_json.get("Events", []):
        for data in event.get("Data", []):
            event_key = (
                data.get("event_text", ""),
                data.get("start_date", ""),
                data.get("end_date", "")
            )

            if event_key not in existing_events_map:
                extracted_events.append({
                    "event_text": event_key[0],
                    "start_date": event_key[1],
                    "end_date": event_key[2],
                    "links": []
                })
                existing_events_map[event_key] = len(extracted_events) - 1

            current_event = extracted_events[existing_events_map[event_key]]

            for link_info in data.get("links", []):
                url = link_info.get("link", "")
                if not url:
                    continue

                if url in existing_links:
                    print(f"Link already extracted, skipping: {url}")
                    continue

                content = fetch_with_retry(url) or fetch_with_playwright(url)

                if content:
                    soup_data = extract_with_beautifulsoup(content)
                    candidate = soup_data["main_text"]
                    text_ok = massiveweb_filter_wrapper(candidate)

                    if not text_ok:
                        only_p = extract_only_paragraphs(content)
                        text_ok = massiveweb_filter_wrapper(only_p)

                    if text_ok:
                        final_text, final_title = text_ok, soup_data["page_title"]
                    else:
                        print(f"Insufficient text or rejected by BeautifulSoup: {url}")
                else:
                    print(f"No HTML obtained: {url}")

                link_data = {
                    "link": url if url else "",
                    "text": link_info.get("text", ""),
                    "dates": link_info.get("dates", []),
                    "title": final_title if final_title else "",
                    "extracted_text": final_text if final_text else "",
                }

                current_event["links"].append(link_data)
                existing_links.add(url)

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(extracted_events, f, ensure_ascii=False, indent=4)

    print(f"File saved: {output_filename}")

if len(sys.argv) < 3:
    print("Usage: python scrape.py <country> <year>")
    sys.exit(1)

country = sys.argv[1]
year = sys.argv[2]
json_file = f"{country}/{year}_in_{country}_events.json"

if not os.path.exists(json_file):
    print(f"File not found: {json_file}")
    sys.exit(1)

events_json = read_json(json_file)
scrape_events(events_json, year, country)
