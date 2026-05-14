import os
import json
import pprint
import re
import base64
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

start = time.time()

pp = pprint.PrettyPrinter(indent=2)
current_dir = os.getcwd()
os.chdir("../../env/")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def clean_string(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    url_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    text = re.sub(url_pattern, "", text)
    text = re.sub(r"\*", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


logs = []


def get_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                return part["body"].get("data")

    else:
        return payload.get("body", {}).get("data")

    logs.append(payload)
    return None


def decode_message(messages):
    print("Decoding the messages...")
    good_messages = []
    for message in messages:
        payload = message["payload"]
        labels = message["labelIds"]
        data = get_body(payload)
        if data is None:
            print("'NoneType' object just passed by...")
            continue
        data = base64.urlsafe_b64decode(data)
        message = clean_string(data)

        if "SPAM" in labels:
            label = "SPAM"
        else:
            label = "BEEF"

        good_messages.append(
            {"messages": message, "labels": labels, "label": label})
    return good_messages


def collect_mails(service):
    messages = []
    full_format = []

    # This doesn't take all the mails, query.
    # q="newer_than:1d" for emails newer than 1 day.
    response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=500, includeSpamTrash=True)
        .execute()
    )
    if "messages" in response:
        messages.extend(response["messages"])
    while "nextPageToken" in response:
        nextpage = response["nextPageToken"]
        response = (
            service.users()
            .messages()
            .list(
                userId="me", pageToken=nextpage, maxResults=500, includeSpamTrash=True
            )
            .execute()
        )
        if "messages" in response:
            messages.extend(response["messages"])

    pp.pprint(messages[:5])
    print(".\n.\n.")
    print("Fetching all emails...")
    print("This may take long...")

    # Fetching each messages
    for msg in messages:
        result = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        full_format.append(result)

    return full_format


def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        print("Credentials loaded successfully...")
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        print("Authorized successfully...")
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            token.close()
        print("Token saved: ", os.path.join(os.getcwd(), "token.json"))

    service = build("gmail", "v1", credentials=creds)
    print("Service built successfully...")

    messages = collect_mails(service)
    decoded_messages = decode_message(messages)
    with open("logs/emails.json", "w") as f:
        json.dump(decoded_messages, f)
        f.close()
    print("Messages saved: ", os.path.join(os.getcwd(), "logs/emails.json"))

    # Saving those unsuccessfull payload - logs
    with open("logs/payloads.json", "w") as f:
        json.dump(logs, f)
        f.close()
    print("Unsuccessfull payloads: ", os.path.join(
        os.getcwd(), "logs/payloads.json"))
    runtime = time.time() - start
    print("Finished.")
    print(f"Runtime: {runtime}")


main()
