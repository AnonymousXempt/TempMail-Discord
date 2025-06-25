import requests

BASE_URL = "https://api.internal.temp-mail.io/api/v3"

def generate_new_email():
    response = requests.post(f"{BASE_URL}/email/new")
    if response.status_code == 200:
        return response.json().get("email")
    raise Exception(f"Failed to generate email: {response.status_code}")

def retrieve_emails(email):
    response = requests.get(f"{BASE_URL}/email/{email}/messages")
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Failed to retrieve emails: {response.status_code} - {response.text}")