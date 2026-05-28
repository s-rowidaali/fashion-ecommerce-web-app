"""
Web scraper for collecting women's fashion ecommerce data
Supports: BeautifulSoup, eBay API, Selenium
Extracted from: draft1_103 (2).ipynb
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import subprocess
import sys
from urllib.parse import unquote
import os
import base64

# Install required packages
try:
    import selenium
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "selenium", "webdriver-manager"])

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# eBay API Credentials (from notebook)
APP_ID = "YOUR_EBAY_APP_ID"
CERT_ID = "YOUR_EBAY_CERT_ID"
# ============================================================================
# HELPER FUNCTIONS (from notebook)
# ============================================================================

fashion_keywords = [
    "dress", "skirt", "top", "blouse", "shirt", "t-shirt",
    "hoodie", "jacket", "coat", "sweater", "jeans", "pants",
    "leggings", "abaya", "hijab", "scarf", "swimwear",
    "bag", "handbag", "backpack", "shoes", "shoe", "sneakers",
    "heels", "heel", "boots", "sandals", "veil", "purse"
]

def get_category_from_text(name, link=""):
    """Categorize product based on name and link text"""
    text = (str(name) + " " + str(link)).lower()

    if any(word in text for word in ["hoodie", "jacket", "coat", "sweater", "cardigan", "blazer"]):
        return "Outerwear"
    elif any(word in text for word in ["dress", "gown"]):
        return "Dresses"
    elif any(word in text for word in ["skirt", "jeans", "pants", "leggings", "trousers", "shorts"]):
        return "Bottoms"
    elif any(word in text for word in ["top", "blouse", "shirt", "t-shirt", "tshirt", "tank"]):
        return "Tops"
    elif any(word in text for word in ["hijab", "scarf", "veil", "abaya", "kaftan", "shawl"]):
        return "Modest Wear"
    elif any(word in text for word in ["bag", "handbag", "backpack", "purse", "tote", "crossbody"]):
        return "Bags"
    elif any(word in text for word in ["shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "heel", "heels", "sandals", "flats"]):
        return "Shoes"
    elif any(word in text for word in ["swimwear", "swimsuit", "bikini", "beachwear"]):
        return "Swimwear"
    else:
        return "Women Fashion"

def is_women_fashion(name, link=""):
    """Check if product is women's fashion"""
    text = (str(name) + " " + str(link)).lower()
    return any(word in text for word in fashion_keywords)

# ============================================================================
# BEAUTIFULSOUP SCRAPER
# ============================================================================

def scrape_beautifulsoup():
    """Scrape products from scrapingcourse.com (exact code from notebook)"""
    print("[BeautifulSoup] Starting scraper...")
    
    base_url = "https://www.scrapingcourse.com/ecommerce/page/"
    site_url = "https://www.scrapingcourse.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    products = []

    for page in range(1, 15):
        url = base_url + str(page)
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("li", class_="product")

        for item in items:
            try:
                name = item.find("h2").text.strip()
                price = item.find("span", class_="price").text.strip()
                link = item.find("a")["href"]
                image = item.find("img")["src"]

                if link.startswith("/"):
                    link = site_url + link

                if image.startswith("/"):
                    image = site_url + image

                name_lower = name.lower()

                if is_women_fashion(name, link):
                    products.append({
                        "Name": name,
                        "Price": price,
                        "Link": link,
                        "Image": image,
                        "Category": get_category_from_text(name, link),
                        "Source": "BeautifulSoup",
                        "Rating": np.nan,
                        "Reviews": 0
                    })

            except Exception as e:
                pass

        if len(products) >= 200:
            break

    df_scraping = pd.DataFrame(products)
    print(f"[BeautifulSoup] Collected {len(df_scraping)} products")
    return df_scraping

# ============================================================================
# EBAY API SCRAPER
# ============================================================================

def get_ebay_token():
    """Get eBay OAuth token (exact code from notebook)"""
    print("[eBay API] Getting authentication token...")
    
    auth_str = APP_ID.strip() + ":" + CERT_ID.strip()
    encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    response = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + encoded_auth
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        },
        timeout=20
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        print("[eBay API] Token obtained successfully")
        return token

    print("Token error:", response.status_code)
    print(response.text[:300])
    return None


def search_ebay(keyword, token, limit=100, offset=0):
    """Search eBay for products (exact code from notebook)"""
    response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers={
            "Authorization": "Bearer " + token,
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        },
        params={
            "q": keyword,
            "limit": limit,
            "offset": offset
        },
        timeout=30
    )

    if response.status_code != 200:
        return []

    return response.json().get("itemSummaries", [])


def scrape_ebay():
    """Scrape products from eBay API (exact code from notebook)"""
    print("[eBay API] Starting scraper...")
    
    category_queries = {
        "Dresses": [
            "women maxi dress", "women summer dress", "women evening dress",
            "women casual dress", "women floral dress", "women party dress"
        ],
        "Tops": [
            "women blouse", "women crop top", "women t shirt",
            "women tank top", "women long sleeve shirt", "women tunic top"
        ],
        "Bottoms": [
            "women jeans", "women leggings", "women skirt",
            "women pants", "women shorts", "women trousers"
        ],
        "Outerwear": [
            "women hoodie", "women jacket", "women coat",
            "women cardigan", "women blazer", "women sweater"
        ],
        "Bags": [
            "women handbag", "women tote bag", "women shoulder bag",
            "women backpack", "women purse", "women crossbody bag"
        ],
        "Shoes": [
            "women sneakers", "women boots", "women sandals",
            "women heels", "women flats", "women loafers"
        ],
        "Modest Wear": [
            "women hijab", "women scarf", "women abaya",
            "women modest dress", "women kaftan", "women shawl"
        ],
        "Swimwear": [
            "women swimwear", "women swimsuit", "women bikini",
            "women beachwear", "women cover up", "women one piece swimsuit"
        ]
    }

    target_total = 3000
    target_per_category = target_total // len(category_queries)
    
    token = get_ebay_token()
    api_products = []
    seen = set()

    if token:
        for category, queries in category_queries.items():
            category_count = 0

            for keyword in queries:
                if category_count >= target_per_category:
                    break

                for offset in range(0, 5000, 100):
                    if category_count >= target_per_category:
                        break

                    items = search_ebay(keyword, token, limit=100, offset=offset)

                    if len(items) == 0:
                        break

                    for item in items:
                        if category_count >= target_per_category:
                            break

                        name = item.get("title", "")
                        price = item.get("price", {}).get("value", "")
                        currency = item.get("price", {}).get("currency", "")
                        link = item.get("itemWebUrl", "")
                        image = item.get("image", {}).get("imageUrl", "") if item.get("image") else ""

                        key = item.get("itemId", name + link)

                        if name and price and link and image and key not in seen:
                            seen.add(key)

                            api_products.append({
                                "Name": name,
                                "Price": price,
                                "Currency": currency,
                                "Link": link,
                                "Image": image,
                                "Category": category,
                                "Source": "eBay API",
                                "Rating": np.nan,
                                "Reviews": 0
                            })

                            category_count += 1

                    time.sleep(0.15)
    else:
        print("[eBay API] Could not authenticate. Skipping eBay scraper.")
        return pd.DataFrame()

    df_api = pd.DataFrame(api_products)
    print(f"[eBay API] Collected {len(df_api)} products")
    return df_api

# ============================================================================
# SELENIUM SCRAPER
# ============================================================================

def scrape_selenium():
    """Scrape products from Amazon.eg using Selenium (exact code from notebook)"""
    print("[Selenium] Starting scraper...")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    except Exception as e:
        print(f"[Selenium] Could not initialize Chrome driver: {e}")
        return pd.DataFrame()
    
    keywords = [
        "dress", "skirt", "top", "blouse", "shirt", "t-shirt",
        "hoodie", "jacket", "coat", "sweater", "jeans", "pants",
        "leggings", "abaya", "hijab", "scarf", "swimwear",
        "bag", "handbag", "backpack", "shoes", "shoe", "sneakers",
        "heels", "heel", "boots", "sandals"
    ]

    selenium_products = []
    seen = set()

    target_selenium_products = 2000
    max_products_per_keyword = 80

    for keyword in keywords:
        if len(selenium_products) >= target_selenium_products:
            break

        count = 0

        for page in range(1, 6):
            if len(selenium_products) >= target_selenium_products:
                break

            try:
                url = f"https://www.amazon.eg/s?k=women+{keyword}&page={page}"
                driver.get(url)
                time.sleep(2)

                products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

                for item in products:
                    if len(selenium_products) >= target_selenium_products:
                        break

                    try:
                        try:
                            name = item.find_element(By.TAG_NAME, "h2").text.strip()
                        except:
                            name = ""

                        try:
                            link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                        except:
                            link = ""

                        try:
                            image = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                        except:
                            image = ""

                        try:
                            price_whole = item.find_element(By.XPATH, ".//span[@class='a-price-whole']").text
                            try:
                                price_fraction = item.find_element(By.XPATH, ".//span[@class='a-price-fraction']").text
                                price = price_whole + "." + price_fraction
                            except:
                                price = price_whole
                        except:
                            price = ""

                        try:
                            rating = item.find_element(By.XPATH, ".//span[contains(@class,'a-icon-alt')]").get_attribute("innerHTML")
                        except:
                            rating = np.nan

                        try:
                            reviews = item.find_element(By.XPATH, ".//span[contains(@class,'s-underline-text')]").text
                        except:
                            reviews = 0

                        if name != "" and link != "" and image != "":
                            key = name + link

                            if key not in seen:
                                seen.add(key)

                                selenium_products.append({
                                    "Name": name,
                                    "Price": price,
                                    "Link": link,
                                    "Image": image,
                                    "Category": get_category_from_text(name, link),
                                    "Source": "Selenium",
                                    "Rating": rating,
                                    "Reviews": reviews
                                })

                                count += 1

                        if count >= max_products_per_keyword:
                            break

                    except:
                        continue

                if count >= max_products_per_keyword:
                    break
            except Exception as e:
                continue

    driver.quit()
    
    df_selenium = pd.DataFrame(selenium_products)
    print(f"[Selenium] Collected {len(df_selenium)} products")
    return df_selenium

def clean_data(df):
    """Clean and process collected data (exact code from notebook)"""
    print("[Processing] Cleaning data...")
    
    if len(df) == 0:
        return df
    
    df_clean = df.copy()
    
    # Strip whitespace
    df_clean["Name"] = df_clean["Name"].astype(str).str.strip()
    df_clean["Link"] = df_clean["Link"].astype(str).str.strip()
    df_clean["Image"] = df_clean["Image"].astype(str).str.strip()
    df_clean["Category"] = df_clean["Category"].astype(str).str.strip()
    df_clean["Source"] = df_clean["Source"].astype(str).str.strip()
    
    # Remove generic category
    df_clean = df_clean[df_clean["Category"] != "Women Fashion"]
    
    # Clean prices
    df_clean["Price"] = df_clean["Price"].astype(str)
    df_clean["Price"] = df_clean["Price"].str.replace("EGP", "", regex=False)
    df_clean["Price"] = df_clean["Price"].str.replace("$", "", regex=False)
    df_clean["Price"] = df_clean["Price"].str.replace(",", "", regex=False)
    df_clean["Price"] = df_clean["Price"].str.replace("جنيه", "", regex=False)
    df_clean["Price"] = df_clean["Price"].str.replace("N/A", "", regex=False)
    df_clean["Price"] = df_clean["Price"].str.strip()
    df_clean["Price"] = pd.to_numeric(df_clean["Price"], errors="coerce")
    
    # Remove empty/invalid rows
    df_clean = df_clean[df_clean["Name"] != ""]
    df_clean = df_clean[df_clean["Link"] != ""]
    df_clean = df_clean[df_clean["Image"] != ""]
    df_clean = df_clean[df_clean["Category"] != ""]
    df_clean = df_clean[df_clean["Source"] != ""]
    
    # Decode URL-encoded names
    df_clean["Name"] = df_clean["Name"].apply(lambda x: unquote(str(x)))
    df_clean["Link"] = df_clean["Link"].astype(str)
    df_clean["Image"] = df_clean["Image"].astype(str)
    
    # Remove duplicates
    df_clean = df_clean.drop_duplicates(subset=["Name", "Link"])
    df_clean = df_clean.reset_index(drop=True)
    
    # Keep only needed columns
    needed_cols = ["Name", "Price", "Link", "Image", "Category", "Source", "Rating", "Reviews"]
    for col in needed_cols:
        if col not in df_clean.columns:
            df_clean[col] = np.nan
    
    df_clean = df_clean[needed_cols]
    
    print(f"[Processing] Cleaned data: {len(df_clean)} products")
    return df_clean


def scrape_all(output_file="women_fashion_clean_data.csv"):
    """Run all scrapers and save combined data (exact logic from notebook)"""
    print("=" * 60)
    print("STARTING FASHION ECOMMERCE DATA SCRAPER")
    print("=" * 60)
    
    frames = []
    
    # BeautifulSoup scraper
    print("\n[1/3] Running BeautifulSoup scraper...")
    df_scraping = scrape_beautifulsoup()
    if len(df_scraping) > 0:
        frames.append(df_scraping)
        print(f"BeautifulSoup products: {len(df_scraping)}")
    
    # eBay scraper
    print("\n[2/3] Running eBay API scraper...")
    df_api = scrape_ebay()
    if len(df_api) > 0:
        frames.append(df_api)
        print(f"eBay API products: {len(df_api)}")
    
    # Selenium scraper
    print("\n[3/3] Running Selenium scraper...")
    df_selenium = scrape_selenium()
    if len(df_selenium) > 0:
        frames.append(df_selenium)
        print(f"Selenium products: {len(df_selenium)}")
    
    if len(frames) == 0:
        print("ERROR: No data was collected from any scraper!")
        return None
    
    # Combine data
    print("\n[Processing] Combining data from all sources...")
    df_all = pd.concat(frames, ignore_index=True)
    print(f"[Processing] Combined total before cleaning: {len(df_all)} products")
    
    # Ensure all columns exist
    needed_cols = ["Name", "Price", "Link", "Image", "Category", "Source", "Rating", "Reviews"]
    for col in needed_cols:
        if col not in df_all.columns:
            df_all[col] = np.nan
    
    df_all = df_all[needed_cols]
    
    # Clean data
    df_clean = clean_data(df_all)
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_clean.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✓ Data saved to: {output_path}")
    print("=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    
    # Print final statistics (from notebook)
    print(f"\nProject Insights")
    print(f"----------------")
    print(f"Total products collected: {len(df_clean)}")
    print(f"Number of categories: {df_clean['Category'].nunique()}")
    print(f"Number of sources: {df_clean['Source'].nunique()}")
    print(f"Most common category: {df_clean['Category'].value_counts().idxmax()}")
    print(f"Most used source: {df_clean['Source'].value_counts().idxmax()}")
    
    df_price = df_clean.dropna(subset=['Price'])
    if len(df_price) > 0:
        print(f"Average price: {round(df_price['Price'].mean(), 2)}")
        print(f"Highest price: {df_price['Price'].max()}")
        print(f"Lowest price: {df_price['Price'].min()}")
    
    return df_clean

if __name__ == "__main__":
    # Run scraper
    df = scrape_all()
    
    if df is not None:
        print(f"\nFinal Statistics:")
        print(f"  Total Products: {len(df)}")
        print(f"  Categories: {df['Category'].nunique()}")
        print(f"  Sources: {df['Source'].nunique()}")
        print(f"  Price Range: ${df['Price'].min():.2f} - ${df['Price'].max():.2f}")
