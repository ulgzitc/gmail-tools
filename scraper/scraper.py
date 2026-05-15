import os
import re
import time
import json
import base64
import pprint
import loadbar
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

pp = pprint.PrettyPrinter(indent=2)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def clean_string(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    url_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    text = re.sub(url_pattern, "", text)
    text = re.sub(r"\*", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                return part["body"].get("data")

    else:
        return payload.get("body", {}).get("data")

    return None


def decode_message(messages):
    bar = loadbar.LoadBar(max=len(messages))
    bar.start()
    print("Decoding the messages...")
    good_messages = []
    for step, message in enumerate(messages):
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
        bar.update(step=step)
    bar.end()
    return good_messages


def collect_mails(service, query):
    messages = []
    full_format = []

    response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=500, includeSpamTrash=True, q=query)
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
                userId="me",
                pageToken=nextpage,
                maxResults=500,
                includeSpamTrash=True,
                q=query,
            )
            .execute()
        )
        if "messages" in response:
            messages.extend(response["messages"])

    pp.pprint(messages[:5])
    print(".\n.\n.")
    print("Fetching all emails...")

    # Fetching each messages
    bar = loadbar.LoadBar(max=len(messages))
    bar.start()
    for step, msg in enumerate(messages):
        result = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        full_format.append(result)
        bar.update(step=step)

    bar.end()
    return full_format


def collect(token_path, creds_path, output_path, port, query):
    start = time.time()
    creds = None
    if token_path is not None:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        print("Credentials loaded successfully...")
    elif not creds and creds_path is not None:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=port)
        print("Authorized successfully...")
        path = os.path.join(os.path.dirname(creds_path), "token.json")
        with open(path, "w") as token:
            token.write(creds.to_json())
            token.close()
        print(
            "New token saved to:",
            path,
            "\n"
            "You can use the token next time [-t path/to/token.json], but expires at ~1 hour.",
        )

    else:
        print(
            "Credentials are not given. Please use [-c path/to/creds.json] or [-t path/to/token.json]"
        )
        return

    service = build("gmail", "v1", credentials=creds)
    print("Service built successfully...")

    messages = collect_mails(service, query)
    decoded_messages = decode_message(messages)
    if output_path is not None:
        with open(output_path, "w") as f:
            json.dump(decoded_messages, f)
            f.close()
        print("Results saved to:", output_path)
    else:
        pp.pprint(decoded_messages)

    runtime = time.time() - start
    print("Finished.")
    print(f"Total runtime: {runtime:.2f} seconds. a.k.a ~{
          (runtime / 60):.2f} minutes.")
    service.close()
