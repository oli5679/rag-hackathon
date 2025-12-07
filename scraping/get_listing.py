import json
import requests
from bs4 import BeautifulSoup

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
    'verification_banner_dismissed': '1',
    'moreinfocount': '10',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sun+Dec+07+2025+11%3A19%3A08+GMT%2B0000+(Greenwich+Mean+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=98be63e9-734b-4d1b-b6c4-b58e1913afb5&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=%3B&AwaitingReconsent=false',
    '_ga': 'GA1.3.901444094.1765105835',
    'advert_view_count': '3',
    '_dc_gtm_UA-100499283-1': '1',
    '_dc_gtm_UA-1921094-1': '1',
    '_ga_YVW611JZH6': 'GS2.1.s1765105835$o1$g1$t1765106747$j60$l0$h0',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'priority': 'u=0, i',
    'referer': 'https://www.spareroom.co.uk/flatshare/?offset=200&search_id=1400724683&sort_by=by_day&mode=list',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    # 'cookie': 'cc=ES; browser_ident=_i4-bc0asLZcQBqpMsU3BQ; experiment_buckets=42-3__1765105833; session_type=known; time_arrived_stamp=1765105835420; OptanonAlertBoxClosed=2025-12-07T11:10:37.571Z; _gid=GA1.3.2093829097.1765105838; _hjSessionUser_313548=eyJpZCI6ImQ0NzhjNmUzLTNjYjMtNWRhYy04MzYxLTIxMWY4NzU2NjllMyIsImNyZWF0ZWQiOjE3NjUxMDU4NDI4NzEsImV4aXN0aW5nIjp0cnVlfQ==; _hjSession_313548=eyJpZCI6ImQ4YWM1MzU4LTUzNmEtNGEzOS1hYjZjLTZhOWZjMGE2NWMxMCIsImMiOjE3NjUxMDU4NDI4NzIsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _hjHasCachedUserAttributes=true; __zlcmid=1Uzo7ZChfHVRkha; _fbp=fb.2.1765105895946.28222949326228376; reg_prompt_shown=1; session_id=642173873; session_key=11560775442353946463; user_id=24743933; new_search_history=1400724255,1400724683; verification_banner_dismissed=1; moreinfocount=10; OptanonConsent=isGpcEnabled=0&datestamp=Sun+Dec+07+2025+11%3A19%3A08+GMT%2B0000+(Greenwich+Mean+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=98be63e9-734b-4d1b-b6c4-b58e1913afb5&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=%3B&AwaitingReconsent=false; _ga=GA1.3.901444094.1765105835; advert_view_count=3; _dc_gtm_UA-100499283-1=1; _dc_gtm_UA-1921094-1=1; _ga_YVW611JZH6=GS2.1.s1765105835$o1$g1$t1765106747$j60$l0$h0',
}

params = {
    'featured': '1',
    'flatshare_id': '15305417',
    'search_id': '1400724683',
    # 'search_results': '/flatshare/?offset=200&search_id=1400724683&sort_by=by_day&mode=list',
}

response = requests.get(
    'https://www.spareroom.co.uk/flatshare/flatshare_detail.pl',
    params=params,
    cookies=cookies,
    headers=headers,
)

with open('listing_response.txt', 'w') as f:
    f.write(response.text)

# Parse with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Extract listing details
listing = {}

# Detail (description)
desc_elem = soup.find('p', class_='detaildesc')
if desc_elem:
    listing['detail'] = desc_elem.get_text(strip=True)

# Key features (property type, location, postcode, station)
key_features = soup.find('ul', class_='key-features')
if key_features:
    features = key_features.find_all('li', class_='key-features__feature')
    for i, f in enumerate(features):
        # Try to determine feature type based on content
        text = f.get_text(strip=True)
        if i == 0:
            listing['property_type'] = text
        elif i == 1:
            listing['location'] = text
        elif i == 2:
            # Postcode - extract just the code part
            listing['postcode'] = text.split()[0] if text else text
        elif i == 3:
            # Station info
            station_name = f.get_text(strip=True).split('Tube map')[0].strip()
            listing['station'] = station_name
            # Station distance
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
            # Clean up key names - normalize whitespace first, then replace special chars
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

# Print parsed data
print('\n=== Parsed Listing ===')
for key, value in listing.items():
    if key == 'detail':
        print(f'\n{key}:\n{value[:500]}...' if len(str(value)) > 500 else f'\n{key}:\n{value}')
    else:
        print(f'{key}: {value}')