#!/usr/bin/env python

"""
DESCRIPTION:
This script reads a CSV file containing a list of data and adds or updates them
in the eLabFTW resources. It ensures that:
- New entries are created if `elabftw_id` is not present in the CSV.
- Existing entries are updated if `elabftw_id` is specified.
- The maintext part is appended to the existing "body" instead of replacing it.

CONFIGURATION:
- Set `API_HOST_URL` to your eLabFTW instance.
- Set `API_KEY` with your API key.
- Define `RESOURCE_CATEGORY_ID` for the correct resource category.
- Ensure `CSV_PATH` points to your CSV file.
"""

import elabapi_python
import csv
import json
import urllib3

# Disable SSL warnings (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#########################
#        CONFIG         #
#########################
# replace with your instance address
API_HOST_URL = 'https://host-url/api/v2'
# replace with your api key
API_KEY = 'your api key'
# this is the resource category where the entries will be created. Visit /api/v2/items_types to GET a list.
RESOURCE_CATEGORY_ID = 1
CSV_PATH = './antibodies.csv'
# path to the csv file, change this too
#########################

# Configure API client
configuration = elabapi_python.Configuration()
configuration.api_key["api_key"] = API_KEY
configuration.api_key_prefix["api_key"] = "Authorization"
configuration.host = API_HOST_URL
configuration.verify_ssl = False

api_client = elabapi_python.ApiClient(configuration)
api_client.set_default_header("Authorization", API_KEY)

itemsApi = elabapi_python.ItemsApi(api_client)


# Function to generate metadata JSON from a CSV row
def get_metadata_from_row(row):
    metadata = {"extra_fields": {}}
    for key, value in row.items():
        field_type = "text"

        # Ignore 'elabftw_id' and 'ID' column to prevent them from being added as metadata
        if key in ["Name", "Maintext", "elabftw_id", "ID"]:
            continue

        if key.lower() == "url":
            field_type = "url"
        elif key.lower() == "price":
            field_type = "number"
        elif key.lower() == "concentration" and value:
            split_conc = value.split()
            metadata["extra_fields"][key] = {
                "value": split_conc[0],
                "type": "number",
                "unit": split_conc[1],
                "units": ["mg/mL", "μg/mL"],
            }
        elif key.lower() == "primary vs secondary":
            metadata["extra_fields"][key] = {
                "value": "Primary",
                "type": "select",
                "options": ["Primary", "Secondary"],
            }
        elif key.lower() == "raised in":
            metadata["extra_fields"][key] = {
                "value": value,
                "type": "select",
                "options": ["Rabbit", "Mouse"],
            }
        elif key.lower() == "recognizes":
            metadata["extra_fields"][key] = {
                "value": value.split(", "),
                "type": "select",
                "allow_multi_values": True,
                "options": [
                    "Ape",
                    "Chicken",
                    "Dog",
                    "Goat",
                    "Guinea Pig",
                    "Hamster",
                    "Human",
                    "Mink",
                    "Monkey",
                    "Mouse",
                    "Rabbit",
                    "Rat",
                    "Sheep",
                    "Zebrafish",
                ],
            }
        else:
            metadata["extra_fields"][key] = {"value": value, "type": field_type}

    return json.dumps(metadata)


# Function to append the new Maintext to the existing body
def get_body_from_row(row, current_body):
    new_comment = row.get("Maintext", "").strip()
    if new_comment:
        return f"{current_body}<p>{new_comment}</p>" if current_body else f"<p>{new_comment}</p>"
    return current_body


###########################################
########### PROCESSING STARTS #############
###########################################

print("Starting import script...")

# Read CSV file
with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
    csvreader = csv.DictReader(csvfile, delimiter=",", quotechar='"')

    for row in csvreader:
        item_id = row.get("elabftw_id", "").strip() or row.get("ID", "").strip()

        if item_id and item_id.isdigit():  # Ensure item_id is a valid integer
            try:
                item_id = int(item_id)  # Ensure it's an integer
                existing_item = itemsApi.get_item(item_id)  # Fetch current item

                print(f"[+] Updating item {item_id}")

                itemsApi.patch_item(
                    item_id,
                    body={
                        "title": row["Name"],
                        "body": get_body_from_row(row, existing_item.body if existing_item.body else ""),
                        "metadata": get_metadata_from_row(row),
                    },
                )
            except Exception as e:
                print(f"[!] Error updating item {item_id}: {e}")

        else:  # Create new item
            print(f"[+] Creating new item in category {RESOURCE_CATEGORY_ID}")

            try:
                response = itemsApi.post_item_with_http_info(
                    body={"category_id": RESOURCE_CATEGORY_ID}
                )
                location_header = response[2].get("Location")
                new_item_id = int(location_header.split("/").pop())

                # Patch the new item with details
                itemsApi.patch_item(
                    new_item_id,
                    body={
                        "title": row["Name"],
                        "body": get_body_from_row(row, ""),
                        "metadata": get_metadata_from_row(row),
                    },
                )

            except Exception as e:
                print(f"[!] Error creating item: {e}")

print("Import completed successfully! 🎉")
