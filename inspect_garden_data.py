import json

def print_garden_data(data):
    if "members" in data:
        for member_uuid, member_data in data["members"].items():
            if "jacobs_contest" in member_data:
                print(f"--- Jacob Data for {member_uuid} ---")
                print(json.dumps(member_data["jacobs_contest"], indent=2))
                break # Just print one member

try:
    with open("tmp/profile_full.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        print_garden_data(data)
except Exception as e:
    print(f"Error: {e}")
