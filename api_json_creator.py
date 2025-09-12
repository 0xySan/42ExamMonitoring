import os
import time
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

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
	"""Generic helper to fetch paginated resources."""
	value = []
	page = 1
	per_page = 50

	while True:
		url = f'{uri}?page={page}&per_page={per_page}'
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
	"""Save {name: id} mappings into JSON, sorted by name."""
	value_map = {values["name"]: values["id"] for values in value}
	sorted_value_map = dict(sorted(value_map.items(), key=lambda item: item[0]))
	with open(filename, "w", encoding="utf-8") as f:
		json.dump(sorted_value_map, f, ensure_ascii=False, indent=4)
	print(f"✅ Saved {len(sorted_value_map)} items to '{filename}'")


def get_exam_results(token, project_id, campus_id=62, date_str=None):
    """Fetch all results for an exam project_id on a given campus & date."""
    if date_str is None:
        date_str = datetime.today().strftime("%Y-%m-%d")

    date_1 = f"{date_str}T01:00:00.205Z"
    date_2 = f"{date_str}T23:00:00.205Z"

    headers = {"Authorization": f"Bearer {token}"}
    results = []
    page = 1
    per_page = 50

    while True:
        url = f"https://api.intra.42.fr/v2/projects/{project_id}/projects_users"
        params = {
            "filter[campus]": campus_id,
            "range[marked_at]": f"{date_1},{date_2}",  # marked_at is key
            "page[size]": per_page,
            "page[number]": page,
        }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise Exception(f"❌ Failed to fetch page {page}: {resp.status_code} {resp.text}")

        page_data = resp.json()
        if not page_data:
            break

        results.extend(page_data)
        page += 1
        time.sleep(0.2)

    return results

def save_exam_results(results, filename="exam_results.json"):
	"""Save simplified exam results {login, status, final_mark} into JSON."""
	cleaned = [
		{
			"login": r["user"]["login"],
			"status": r.get("status", "unknown"),
			"time_marked": r.get("marked_at", None),
			"final_mark": r.get("final_mark", None)
		}
		for r in results
	]
	with open(filename, "w", encoding="utf-8") as f:
		json.dump(cleaned, f, ensure_ascii=False, indent=4)
	print(f"✅ Saved {len(cleaned)} exam results to '{filename}'")


if __name__ == "__main__":
	token = get_access_token()

	# Example usage: campus Le Havre (62), cursus Piscine C (9), exam project id 1301
	campus_id = 62
	cursus_id = 9
	project_id = 1303
	date_str = datetime.today().strftime("%Y-%m-%d")

	results = get_exam_results(token, project_id, campus_id, date_str)
	save_exam_results(results, "exam_results.json")
