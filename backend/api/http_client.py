import requests
import logging

LOGGER = logging.getLogger(__name__)

# Global session for connection pooling
session = requests.Session()
session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20))
session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20))

def get_session():
    return session
