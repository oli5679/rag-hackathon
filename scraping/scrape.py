import re
import csv
import json
import time
import requests
from bs4 import BeautifulSoup

SEARCH_ID = '1400724683'

# Shared cookies and headers
cookies = {
    'cc': 'ES',
    'browser_ident': '_i4-bc0asLZcQBqpMsU3BQ',
    'experiment_buckets': '42-3__1765105833',
    'session_type': 'known',
    'time_arrived_stamp': '1765105835420',
    'OptanonAlertBoxClosed': '2025-12-07T11:10:37.571Z',
    '_gid': 'GA1.3.2093829097.1765105838',
    '_hjSessionUser_313548': 'eyJpZCI6ImQ0NzhjNmUzLTNjYjMtNWRhYy04MzYxLTIxMWY4NzU2NjllMyIsImNyZWF0ZWQiOjE3NjUxMDU4NDI4NzEsImV4aXN0aW5nIjp0cnVlfQ==',
    '_hjSession_313548': 'eyJpZCI6ImQ4YWM1MzU4LTUzNmEtNGEzOS1hYjZjLTZhOWZjMGE2NWMxMCIsImMiOjE3NjUxMDU4NDI4NzIsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=',
    '_hjHasCachedUserAttributes': 'true',
    '__zlcmid': '1Uzo7ZChfHVRkha',
    '_fbp': 'fb.2.1765105895946.28222949326228376',
    'reg_prompt_shown': '1',
    'session_id': '642173873',
    'session_key': '11560775442353946463',
    'user_id': '24743933',
    'new_search_history': '1400724255,1400724683',
    'advert_view_count': '2',
    'verification_banner_dismissed': '1',
    '_dc_gtm_UA-100499283-1': '1',
    '_dc_gtm_UA-1921094-1': '1',
    'moreinfocount': '10',
    '_ga_YVW611JZH6': 'GS2.1.s1765105835$o1$g1$t1765106321$j49$l0$h0',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sun+Dec+07+2025+11%3A18%3A41+GMT%2B0000+(Greenwich+Mean+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=98be63e9-734b-4d1b-b6c4-b58e1913afb5&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=%3B&AwaitingReconsent=false',
    '_ga': 'GA1.3.901444094.1765105835',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
}


def get_flatshare_ids(offset):
    """Fetch flatshare IDs from a search results page."""
    params = {
        'offset': str(offset),
        'search_id': SEARCH_ID,
        'sort_by': 'by_day',
        'mode': 'list',
    }
    response = requests.get(
        'https://www.spareroom.co.uk/flatshare/',
        params=params,
        cookies=cookies,
        headers=headers
    )
    flatshare_ids = re.findall(r'flatshare_id=(\d+)', response.text)
    return list(set(flatshare_ids))


def get_listing_details(flatshare_id):
    """Fetch and parse listing details for a specific flatshare ID."""
    params = {
        'flatshare_id': flatshare_id,
        'search_id': '1400724683',
    }
    response = requests.get(
        'https://www.spareroom.co.uk/flatshare/flatshare_detail.pl',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    
    soup = BeautifulSoup(response.text, 'html.parser')
    listing = {'flatshare_id': flatshare_id}
    
    # Detail (description)
    desc_elem = soup.find('p', class_='detaildesc')
    if desc_elem:
        listing['detail'] = desc_elem.get_text(strip=True)
    
    # Key features (property type, location, postcode, station)
    key_features = soup.find('ul', class_='key-features')
    if key_features:
        features = key_features.find_all('li', class_='key-features__feature')
        for i, f in enumerate(features):
            text = f.get_text(strip=True)
            if i == 0:
                listing['property_type'] = text
            elif i == 1:
                listing['location'] = text
            elif i == 2:
                listing['postcode'] = text.split()[0] if text else text
            elif i == 3:
                station_name = f.get_text(strip=True).split('Tube map')[0].strip()
                listing['station'] = station_name
                distance_elem = f.find('small', class_='key-features__station-distance')
                if distance_elem:
                    listing['station_distance'] = distance_elem.get_text(strip=True)
    
    # Feature sections - extract all key/value pairs as flat features
    feature_sections = soup.find_all('section', class_='feature')
    for section in feature_sections:
        # Special case: price section - the dt contains the rent, dd contains room type
        if 'feature--price_room_only' in section.get('class', []):
            feature_list = section.find('dl', class_='feature-list')
            if feature_list:
                key_elem = feature_list.find('dt', class_='feature-list__key')
                value_elem = feature_list.find('dd', class_='feature-list__value')
                if key_elem:
                    listing['rent'] = key_elem.get_text(strip=True)
                if value_elem:
                    listing['room_type'] = value_elem.get_text(strip=True)
            continue
        
        feature_list = section.find('dl', class_='feature-list')
        if feature_list:
            keys = feature_list.find_all('dt', class_='feature-list__key')
            values = feature_list.find_all('dd', class_='feature-list__value')
            for k, v in zip(keys, values):
                key_text = k.get_text(strip=True)
                value_text = v.get_text(strip=True)
                # Clean up key names - normalize whitespace, remove special chars
                key_name = ' '.join(key_text.split())  # Normalize whitespace
                key_name = key_name.lower().replace(' ', '_').replace('?', '').replace('#', 'num').replace('/', '_')
                listing[key_name] = value_text
    
    # Extract photo URLs from the photo gallery
    photo_links = soup.find_all('a', class_='photo-gallery__thumbnail-link')
    images = []
    for link in photo_links:
        href = link.get('href')
        if href:
            images.append(href)
    listing['images'] = json.dumps(images)
    
    return listing


def main():
    # Step 1: Collect all flatshare IDs
    print("=== Step 1: Collecting flatshare IDs ===")
    all_flatshare_ids = []
    
    for offset in range(0, 990, 10):
        print(f"Fetching offset {offset}...")
        ids = get_flatshare_ids(offset)
        all_flatshare_ids.extend(ids)
        print(f"  Found {len(ids)} IDs (total so far: {len(all_flatshare_ids)})")
        
        if offset < 990:  # Don't sleep after the last request
            time.sleep(5)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for id in all_flatshare_ids:
        if id not in seen:
            seen.add(id)
            unique_ids.append(id)
    
    print(f"\nTotal unique flatshare IDs: {len(unique_ids)}")
    
    # Save IDs to CSV
    with open('flatshare_ids.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['flatshare_id'])
        for id in unique_ids:
            writer.writerow([id])
    print("Saved flatshare IDs to flatshare_ids.csv")
    
    # Step 2: Fetch details for each listing
    print("\n=== Step 2: Fetching listing details ===")
    all_listings = []
    all_keys = set()
    
    for i, flatshare_id in enumerate(unique_ids):
        print(f"Fetching listing {i+1}/{len(unique_ids)}: {flatshare_id}...")
        try:
            listing = get_listing_details(flatshare_id)
            all_listings.append(listing)
            all_keys.update(listing.keys())
        except Exception as e:
            print(f"  Error fetching {flatshare_id}: {e}")
        
        if i < len(unique_ids) - 1:  # Don't sleep after the last request
            time.sleep(1)
    
    # Save listings to CSV
    # Sort keys for consistent column order, but keep flatshare_id first
    sorted_keys = ['flatshare_id'] + sorted(k for k in all_keys if k != 'flatshare_id')
    
    with open(f'listings-{SEARCH_ID}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_keys, extrasaction='ignore')
        writer.writeheader()
        for listing in all_listings:
            writer.writerow(listing)
    
    print(f"\nSaved {len(all_listings)} listings to listings.csv")
    print("Done!")


if __name__ == '__main__':
    main()

