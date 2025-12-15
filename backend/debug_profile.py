
import os
import sys
import django
from django.conf import settings

# Configure Django settings
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from api.domain.profile_summary import summarize_profile

def test_summary():
    print("Testing summarize_profile...")
    try:
        # Mock data
        uuid = "test_uuid"
        profile = {
            "members": {
                "test_uuid": {
                    "leveling": {"experience": 100},
                    "player_data": {"experience": {}},
                    "slayer": {},
                    "dungeons": {},
                    "inventory": {},
                }
            },
            "profile_id": "test_profile",
            "cute_name": "Tomato",
            "game_mode": "normal",
        }
        
        summary = summarize_profile(uuid, profile)
        print("Summary success:", summary is not None)
    except Exception as e:
        print("Summary failed:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_summary()
