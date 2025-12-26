import requests

URLS = [
    "https://api.skyhelper.altpapier.dev/v1",
    "https://skyhelper.altpapier.dev/api",
    "https://api.skyhelper.net",
    "https://skyhelper-api.herokuapp.com",
    "https://api.noahcdn.fr/skyhelper",
    "https://soopy.dev/api/skyblock/networth"
]

PLAYER_UUID = "b876ec32e396476ba1158438d83c67d4"

def check_urls():
    for base_url in URLS:
        url = f"{base_url}/profiles/{PLAYER_UUID}/networth"
        print(f"Testing: {url}")
        try:
            response = requests.get(url, timeout=2)
            print(f"  Status: {response.status_code}")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    check_urls()
