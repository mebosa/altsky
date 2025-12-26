import logging
import requests
from typing import Optional, Dict, Any

LOGGER = logging.getLogger(__name__)

SKYHELPER_API_URL = "https://api.skyhelper.altpapier.dev/v1"

def fetch_networth(profile_id: str, player_uuid: str) -> Optional[Dict[str, Any]]:
    """
    Fetch networth data from SkyHelper API.
    """
    try:
        # Endpoint: /profiles/:uuid/networth
        # Query params: profileId (optional, but good to specify)
        url = f"{SKYHELPER_API_URL}/profiles/{player_uuid}/networth"
        params = {'profileId': profile_id}
        
        # Using GET to fetch from Hypixel via SkyHelper
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data') or data # API structure might vary
        else:
            LOGGER.warning(f"SkyHelper API returned {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        LOGGER.warning(f"Failed to fetch networth from SkyHelper API: {e}")
        return None
