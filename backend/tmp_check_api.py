import os
import requests
from dotenv import load_dotenv, find_dotenv

env_file = find_dotenv()
print(f"Loading env from: {env_file}")
load_dotenv(env_file)

api_key = os.getenv('HYPIXEL_API_KEY')
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key length: {len(api_key)}")
    print(f"API Key start: {api_key[:4]}...")

url = 'https://api.hypixel.net/v2/skyblock/profiles'
uuid = '84473185-b58a-4bc1-8801-ad24110b5db1' # mebosa

try:
    headers = {'API-Key': api_key} if api_key else {}
    print(f"Requesting {url} with headers: {headers.keys()}")
    response = requests.get(url, params={'uuid': uuid}, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
