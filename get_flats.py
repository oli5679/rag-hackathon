import re
import requests

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
    # 'cookie': 'cc=ES; browser_ident=_i4-bc0asLZcQBqpMsU3BQ; experiment_buckets=42-3__1765105833; session_type=known; time_arrived_stamp=1765105835420; OptanonAlertBoxClosed=2025-12-07T11:10:37.571Z; _gid=GA1.3.2093829097.1765105838; _hjSessionUser_313548=eyJpZCI6ImQ0NzhjNmUzLTNjYjMtNWRhYy04MzYxLTIxMWY4NzU2NjllMyIsImNyZWF0ZWQiOjE3NjUxMDU4NDI4NzEsImV4aXN0aW5nIjp0cnVlfQ==; _hjSession_313548=eyJpZCI6ImQ4YWM1MzU4LTUzNmEtNGEzOS1hYjZjLTZhOWZjMGE2NWMxMCIsImMiOjE3NjUxMDU4NDI4NzIsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _hjHasCachedUserAttributes=true; __zlcmid=1Uzo7ZChfHVRkha; _fbp=fb.2.1765105895946.28222949326228376; reg_prompt_shown=1; session_id=642173873; session_key=11560775442353946463; user_id=24743933; new_search_history=1400724255,1400724683; advert_view_count=2; verification_banner_dismissed=1; _dc_gtm_UA-100499283-1=1; _dc_gtm_UA-1921094-1=1; moreinfocount=10; _ga_YVW611JZH6=GS2.1.s1765105835$o1$g1$t1765106321$j49$l0$h0; OptanonConsent=isGpcEnabled=0&datestamp=Sun+Dec+07+2025+11%3A18%3A41+GMT%2B0000+(Greenwich+Mean+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=98be63e9-734b-4d1b-b6c4-b58e1913afb5&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=%3B&AwaitingReconsent=false; _ga=GA1.3.901444094.1765105835',
}

params = {
    'offset': '200',
    'search_id': '1400724683',
    'sort_by': 'by_day',
    'mode': 'list',
}

response = requests.get('https://www.spareroom.co.uk/flatshare/', params=params, cookies=cookies, headers=headers)

with open('response.txt', 'w') as f:
    f.write(response.text)

# Extract all flatshare IDs
flatshare_ids = re.findall(r'flatshare_id=(\d+)', response.text)
unique_ids = list(set(flatshare_ids))

print(f'Found {len(unique_ids)} unique flatshare IDs:')
for id in unique_ids:
    print(id)