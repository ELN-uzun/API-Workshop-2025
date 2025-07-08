#!/usr/bin/env python

###############
# DESCRIPTION #
##############
#
# This script reads a CSV file containing a list of experiments
# and either creates new experiments or updates existing ones.
#

import elabapi_python
import csv
import json
import urllib3

# Disable SSL warnings (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#########################
#        CONFIG         #
#########################
API_HOST_URL = 'https://host-url/api/v2'
# Replace with your instance URL
API_KEY = 'your api key'
# Replace with your API key
CSV_PATH = './antibodies_2.csv'
# Path to CSV file
#########################

# Configure the API client
configuration = elabapi_python.Configuration()
configuration.api_key['api_key'] = API_KEY
configuration.api_key_prefix['api_key'] = 'Authorization'
configuration.host = API_HOST_URL
configuration.debug = False
configuration.verify_ssl = False

api_client = elabapi_python.ApiClient(configuration)
api_client.set_default_header(header_name='Authorization', header_value=API_KEY)

experimentApi = elabapi_python.ExperimentsApi(api_client)

# Function to generate metadata JSON from a CSV row
def getMetadataFromRow(row):
    metadata = {'extra_fields': {}}
    for key, value in row.items():
        field_type = 'text'
        if key in ['Name', 'Maintext', 'elabftw_id', 'ID']:
            continue

        if key.lower() == 'url':
            field_type = 'url'
        elif key.lower() == 'price':
            field_type = 'number'
        elif key.lower() == 'concentration' and value:
            split_conc = value.split()
            metadata['extra_fields'][key] = {
                'value': split_conc[0],
                'type': 'number',
                'unit': split_conc[1],
                'units': ['mg/mL', 'μg/mL']
            }
        elif key.lower() == 'primary vs secondary':
            metadata['extra_fields'][key] = {
                'value': 'Primary',
                'type': 'select',
                'options': ['Primary', 'Secondary']
            }
        elif key.lower() == 'raised in':
            metadata['extra_fields'][key] = {
                'value': value,
                'type': 'select',
                'options': ['Rabbit', 'Mouse']
            }
        elif key.lower() == 'recognizes':
            metadata['extra_fields'][key] = {
                'value': value.split(', '),
                'type': 'select',
                'allow_multi_values': True,
                'options': [
                    'Ape', 'Chicken', 'Dog', 'Goat', 'Guinea Pig', 'Hamster',
                    'Human', 'Mink', 'Monkey', 'Mouse', 'Rabbit', 'Rat', 'Sheep', 'Zebrafish'
                ]
            }
        else:
            metadata['extra_fields'][key] = {'value': value, 'type': field_type}

    return json.dumps(metadata)

# Function to append new Maintext to the existing body
def getBodyFromRow(row, current_body):
    new_text = row.get("Maintext", "").strip()
    if new_text:
        return f"{current_body}<p>{new_text}</p>" if current_body else f"<p>{new_text}</p>"
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

        if item_id and item_id.isdigit():  # Check if item_id is a valid integer
            try:
                item_id = int(item_id)  # Convert to integer
                existing_experiment = experimentApi.get_experiment(item_id)  # Fetch existing experiment

                print(f"[+] Updating existing experiment {item_id}")

                experimentApi.patch_experiment(
                    item_id,
                    body={
                        "title": row["Name"],
                        "body": getBodyFromRow(row, existing_experiment.body if existing_experiment.body else ""),
                        "custom_id": row.get("ID", ""),
                        "metadata": getMetadataFromRow(row),
                    },
                )
            except Exception as e:
                print(f"[!] Error updating experiment {item_id}: {e}")

        else:  # Create new experiment
            print(f"[+] Creating new experiment")

            try:
                response = experimentApi.post_experiment_with_http_info(body={})
                location_header = response[2].get("Location")
                new_item_id = int(location_header.split("/").pop())

                # Patch the new experiment with details
                experimentApi.patch_experiment(
                    new_item_id,
                    body={
                        "title": row["Name"],
                        "body": getBodyFromRow(row, ""),
                        "custom_id": row.get("ID", ""),
                        "metadata": getMetadataFromRow(row),
                    },
                )

            except Exception as e:
                print(f"[!] Error creating experiment: {e}")

print("Import completed successfully! 🎉")
