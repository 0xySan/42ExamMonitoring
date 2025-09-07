import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

UID = os.getenv("UID")
SECRET = os.getenv("SECRET")

if not UID or not SECRET:
	raise Exception("UID or SECRET not set in .env file")

def get_access_token():
	url = "https://api.intra.42.fr/oauth/token"
	data = {
		"grant_type": "client_credentials",
		"client_id": UID,
		"client_secret": SECRET
	}
	resp = requests.post(url, data=data)
	resp.raise_for_status()
	return resp.json()["access_token"]

def get_all(token, uri=f"https://api.intra.42.fr/v2/campus"):
	value = []
	page = 1
	per_page = 50

	while True:
		url=f'{uri}?page={page}&per_page={per_page}'
		headers = {"Authorization": f"Bearer {token}"}
		resp = requests.get(url, headers=headers)

		if resp.status_code == 429:
			retry_after = int(resp.headers.get("Retry-After", 2))
			print(f"⏳ Rate limited. Sleeping for {retry_after} seconds...")
			time.sleep(retry_after)
			continue

		resp.raise_for_status()
		data = resp.json()

		if not data:
			break

		value.extend(data)
		page += 1
		time.sleep(0.5)

	return value

def save_ids_to_json(value, filename="campuses.json"):
	# Extract name and id
	value_map = {values["name"]: values["id"] for values in value}
	# Save to file
	with open(filename, "w", encoding="utf-8") as f:
		json.dump(value_map, f, ensure_ascii=False, indent=4)
	print(f"✅ Saved {len(value_map)} campuses to '{filename}'")

# if __name__ == "__main__":
# 	token = get_access_token()
# 	with open("campuses.json", "r") as f:
# 		campus_map = json.load(f)
# 		campus_id = campus_map.get("Le Havre")
# 	with open("cursus.json", "r") as f:
# 		cursus_map = json.load(f)
# 		cursus_id = cursus_map.get("Piscine C")
# 	exams = get_all(token, f"https://api.intra.42.fr/v2/campus/{campus_id}/cursus/{cursus_id}/exams")
# 	save_ids_to_json(exams, "exams.json")
