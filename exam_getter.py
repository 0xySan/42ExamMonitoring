import os
import time
import requests
import json
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

def get_all_exams(token, campus):
	exams = []
	page = 1
	per_page = 50

	while True:
		url = f"https://api.intra.42.fr/v2/cursus?page={page}&per_page={per_page}"
		headers = {"Authorization": f"Bearer {token}"}
		resp = requests.get(url, headers=headers)
		# Handle 429 - too many requests
		if resp.status_code == 429:
			retry_after = int(resp.headers.get("Retry-After", 2))
			print(f"⏳ Rate limited. Sleeping for {retry_after} seconds...")
			time.sleep(retry_after)
			continue
		resp.raise_for_status()
		data = resp.json()
		if not data:
			break
		print(data)
		exams.extend(data)
		page += 1
		time.sleep(0.5)

	return exams


if __name__ == "__main__":
	token = get_access_token()
	with open("campuses.json", "r") as f:
		campus_map = json.load(f)
		campus_id = campus_map.get("Le Havre")
	exams = get_all_exams(token, campus_id)
