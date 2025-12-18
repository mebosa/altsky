import os
from dotenv import load_dotenv

# Explicitly load .env from current dir
load_dotenv('.env')

api_key = os.getenv('HYPIXEL_API_KEY')
print(f"Root API Key start: {api_key[:4] if api_key else 'None'}...")
