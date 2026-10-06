import logging
import re
import urllib.request
from typing import List, Optional, Set
from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict
import pandas as pd
import argparse
import platform
import time
import os

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
IGNORED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.pdf', '.css', '.js', '.ts', '.ico')
IGNORED_DOMAINS = (
    'sentry.io', 'wixpress.com', 'example.com', 'domain.com', 'schema.org', 
    'google.com', 'googleapis.com', 'facebook.com', 'twitter.com', 'instagram.com',
    'sentry-cdn.com', 'w3.org'
)
IGNORED_PREFIXES = ('user@', 'email@', 'name@', 'info@domain', 'yourname@', 'contact@domain')

def extract_emails_from_html(html: str) -> Set[str]:
    found_emails = set()
    matches = re.findall(EMAIL_REGEX, html)
    for email in matches:
        email_lower = email.lower().strip()
        if any(email_lower.endswith(ext) for ext in IGNORED_EXTENSIONS):
            continue
        if any(dom in email_lower for dom in IGNORED_DOMAINS):
            continue
        if any(email_lower.startswith(pref) for pref in IGNORED_PREFIXES):
            continue
        found_emails.add(email_lower)
    return found_emails

def extract_email_from_website(website_url: str) -> str:
    if not website_url:
        return ""
    
    url = website_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    found_emails = set()

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            found_emails.update(extract_emails_from_html(html))
    except Exception as e:
        logging.debug(f"Could not fetch homepage {url}: {e}")

    if not found_emails:
        base_url = url.rstrip('/')
        for path in ['/contact', '/contact-us', '/about', '/about-us']:
            try:
                target_url = base_url + path
                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    extracted = extract_emails_from_html(html)
                    if extracted:
                        found_emails.update(extracted)
                        break
            except Exception:
                pass

    return ", ".join(sorted(found_emails)) if found_emails else ""

@dataclass
class Place:
    name: str = ""
    address: str = ""
    website: str = ""
    email: str = ""
    phone_number: str = ""
    reviews_count: Optional[int] = None
    reviews_average: Optional[float] = None
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    store_delivery: str = "No"
    place_type: str = ""
    opens_at: str = ""
    introduction: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def extract_text(page: Page, xpath: str) -> str:
    try:
        if page.locator(xpath).count() > 0:
            return page.locator(xpath).inner_text()
    except Exception as e:
        logging.warning(f"Failed to extract text for xpath {xpath}: {e}")
    return ""

def extract_place(page: Page) -> Place:
    name_xpath = '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]'
    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
    reviews_count_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'
    reviews_average_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'
    info1 = '//div[@class="LTs0Rc"][1]'
    info2 = '//div[@class="LTs0Rc"][2]'
    info3 = '//div[@class="LTs0Rc"][3]'
    opens_at_xpath = '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]'
    opens_at_xpath2 = '//div[@class="MkV9"]//span[@class="ZDu9vd"]//span[2]'
    place_type_xpath = '//div[@class="LBgpqf"]//button[@class="DkEaL "]'
    intro_xpath = '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]'

    place = Place()
    place.name = extract_text(page, name_xpath)
    place.address = extract_text(page, address_xpath)
    place.website = extract_text(page, website_xpath)
    raw_phone = extract_text(page, phone_number_xpath)
    place.phone_number = raw_phone.lstrip('+').strip() if raw_phone else ""
    place.place_type = extract_text(page, place_type_xpath)
    place.introduction = extract_text(page, intro_xpath) or "None Found"

    page_text = extract_text(page, '//div[@class="TIHn2 "]')
    card_emails = extract_emails_from_html(page_text)
    if card_emails:
        place.email = ", ".join(sorted(card_emails))
    elif place.website:
        logging.info(f"Extracting email from website: {place.website}")
        place.email = extract_email_from_website(place.website)

    reviews_count_raw = extract_text(page, reviews_count_xpath)
    if reviews_count_raw:
        try:
            temp = reviews_count_raw.replace('\xa0', '').replace('(','').replace(')','').replace(',','')
            place.reviews_count = int(temp)
        except Exception as e:
            logging.warning(f"Failed to parse reviews count: {e}")

    reviews_avg_raw = extract_text(page, reviews_average_xpath)
    if reviews_avg_raw:
        try:
            temp = reviews_avg_raw.replace(' ','').replace(',','.')
            place.reviews_average = float(temp)
        except Exception as e:
            logging.warning(f"Failed to parse reviews average: {e}")

    for idx, info_xpath in enumerate([info1, info2, info3]):
        info_raw = extract_text(page, info_xpath)
        if info_raw:
            temp = info_raw.split('·')
            if len(temp) > 1:
                check = temp[1].replace("\n", "").lower()
                if 'shop' in check:
                    place.store_shopping = "Yes"
                if 'pickup' in check:
                    place.in_store_pickup = "Yes"
                if 'delivery' in check:
                    place.store_delivery = "Yes"

    opens_at_raw = extract_text(page, opens_at_xpath)
    if opens_at_raw:
        opens = opens_at_raw.split('⋅')
        if len(opens) > 1:
            place.opens_at = opens[1].replace("\u202f","")
        else:
            place.opens_at = opens_at_raw.replace("\u202f","")
    else:
        opens_at2_raw = extract_text(page, opens_at_xpath2)
        if opens_at2_raw:
            opens = opens_at2_raw.split('⋅')
            if len(opens) > 1:
                place.opens_at = opens[1].replace("\u202f","")
            else:
                place.opens_at = opens_at2_raw.replace("\u202f","")
    return place

def scrape_places(search_for: str, total: int) -> List[Place]:
    setup_logging()
    places: List[Place] = []
    with sync_playwright() as p:
        if platform.system() == "Windows":
            browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            browser = p.chromium.launch(executable_path=browser_path, headless=False)
        else:
            browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto("https://www.google.com/maps/@32.9817464,70.1930781,3.67z?", timeout=60000)
            page.wait_for_timeout(1000)
            page.locator("//form[contains(@jsaction,'searchboxFormSubmit')]//input[@name='q']").fill(search_for)
            page.keyboard.press("Enter")
            page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')
            previously_counted = 0
            while True:
                page.mouse.wheel(0, 10000)
                page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')
                found = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                logging.info(f"Currently Found: {found}")
                if found >= total:
                    break
                if found == previously_counted:
                    logging.info("Arrived at all available")
                    break
                previously_counted = found
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
            listings = [listing.locator("xpath=..") for listing in listings]
            logging.info(f"Total Found: {len(listings)}")
            for idx, listing in enumerate(listings):
                try:
                    listing.click()
                    page.wait_for_selector('//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]', timeout=10000)
                    time.sleep(1.5)
                    place = extract_place(page)
                    if place.name:
                        places.append(place)
                    else:
                        logging.warning(f"No name found for listing {idx+1}, skipping.")
                except Exception as e:
                    logging.warning(f"Failed to extract listing {idx+1}: {e}")
        finally:
            browser.close()
    return places

def convert_csv_to_excel(csv_path: str, excel_path: Optional[str] = None) -> str:
    if not os.path.exists(csv_path):
        logging.error(f"CSV file not found: {csv_path}")
        return ""
    if not excel_path:
        excel_path = os.path.splitext(csv_path)[0] + ".xlsx"
    raw_df = pd.read_csv(csv_path)

    df = pd.DataFrame()
    col_map = {
        'Name': ['name', 'Name'],
        'Email': ['email', 'Email'],
        'Category': ['place_type', 'Category', 'category'],
        'Phone Number': ['phone_number', 'Phone Number', 'phone'],
        'Website': ['website', 'Website']
    }

    for target_name, possible_sources in col_map.items():
        found = False
        for src in possible_sources:
            if src in raw_df.columns:
                df[target_name] = raw_df[src]
                found = True
                break
        if not found:
            df[target_name] = ""

    df.to_excel(excel_path, index=False, engine='openpyxl')
    logging.info(f"Successfully converted '{csv_path}' to Excel sheet '{excel_path}'")
    return excel_path

def save_places_to_excel(places: List[Place], output_path: str = "result.xlsx", overwrite: bool = False):
    raw_df = pd.DataFrame([asdict(place) for place in places])
    if raw_df.empty:
        logging.warning("No data to save. DataFrame is empty.")
        return

    column_mapping = [
        ('name', 'Name'),
        ('email', 'Email'),
        ('place_type', 'Category'),
        ('phone_number', 'Phone Number'),
        ('website', 'Website')
    ]

    new_df = pd.DataFrame()
    for src_col, dest_col in column_mapping:
        if src_col in raw_df.columns:
            new_df[dest_col] = raw_df[src_col]
        else:
            new_df[dest_col] = ""

    if not output_path.lower().endswith(".xlsx"):
        output_path = os.path.splitext(output_path)[0] + ".xlsx"

    if os.path.exists(output_path) and not overwrite:
        try:
            existing_df = pd.read_excel(output_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.drop_duplicates(subset=['Name', 'Phone Number', 'Website'], keep='first', inplace=True)
            final_df = combined_df
            logging.info(f"Appended new results! Total rows in '{output_path}': {len(final_df)}")
        except Exception as e:
            logging.warning(f"Could not read existing Excel file for append: {e}")
            final_df = new_df
    else:
        final_df = new_df
        logging.info(f"Saved {len(final_df)} places to Excel Sheet: '{output_path}'")

    if 'Phone Number' in final_df.columns:
        final_df['Phone Number'] = final_df['Phone Number'].astype(str).str.replace(r'^\+', '', regex=True).str.strip()

    final_df.to_excel(output_path, index=False, engine='openpyxl')

def main():
    parser = argparse.ArgumentParser(description="Google Maps Scrapper with Excel Export")
    parser.add_argument("-s", "--search", type=str, help="Search query for Google Maps")
    parser.add_argument("-t", "--total", type=int, help="Total number of results to scrape")
    parser.add_argument("-o", "--output", type=str, default="result.xlsx", help="Output Excel file path (.xlsx)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing Excel file instead of appending")
    args = parser.parse_args()

    setup_logging()

    search_for = args.search or "turkish stores in toronto Canada"
    total = args.total or 1
    output_path = args.output
    places = scrape_places(search_for, total)
    save_places_to_excel(places, output_path, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
