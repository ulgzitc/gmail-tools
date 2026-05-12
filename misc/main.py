import os
import re
import pprint
import joblib
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

pp = pprint.PrettyPrinter(indent=2)

transformer = joblib.load("../model/transformer.pkl")
model = joblib.load("../model/simple.pkl")

os.chdir("../../env/")
current_path = os.getcwd()

SCOPES = ["https://www.googleapis.com/auth/gmail.modify",
          "https://mail.google.com/"]


def predict(text):
    x = transformer.transform(text)
    pred = model.predict(x)
    return pred


def parse_msg(msg):
    payload = msg.get("payload")
    parts = payload.get("parts")[0]
    if "data" in parts["body"]:
        data = parts["body"]["data"].replace("-", "+").replace("_", "/")
    else:
        return 1
    return base64.urlsafe_b64decode(data)


def clear_string(rawtext):
    if isinstance(rawtext, bytes):
        text = rawtext.decode("utf-8", errors="ignore")
    else:
        text = rawtext

    url_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    text = re.sub(url_pattern, "", text)
    text = re.sub(r"\*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    gmail_service = build("gmail", "v1", credentials=creds)

    results = (
        gmail_service.users().messages().list(userId="me", q="is:unread").execute()
    )
    messages = results.get("messages", [])
    for msg in messages:
        m = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        text = parse_msg(m)
        if text == 1:
            continue
        fintext = [clear_string(text)]
        result = predict(fintext)
        print(fintext[0])
        print("Label: ", result, "\n\n")

    gmail_service.close()


main()
