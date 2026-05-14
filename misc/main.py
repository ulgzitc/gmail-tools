import os
import re
import pprint
import joblib
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

pp = pprint.PrettyPrinter(indent=2)

transformer = joblib.load("../spam-filter/model/transformer.pkl")
model = joblib.load("../spam-filter/model/simple.pkl")

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
    try:
        parts = payload.get("parts")[0]
    except:
        print("Here you got error with that parts part")
        return 1
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


def modify(service, msg_id, label_id):
    mod_object = {
        "addLabelIds": [label_id],
    }
    service.users().messages().modify(userId="me", id=msg_id, body=mod_object).execute()


def create_label(service, label_name):
    label_object = {
        "name": label_name,
        "messageListVisibility": "show",
        "labelListVisibility": "labelShow",
        "type": "user",
    }
    try:
        label = (
            service.users().labels().create(userId="me", body=label_object).execute()
        )
        print(f"Label created: {label['id']}")
        return label["id"]
    except Exception as exx:
        print(
            f"Ehh bro, error here, maybe you already had this shit but I don't think google names their labels WAHOOOO, so, {
                exx
            }'"
        )
        results = service.users().labels().list(userId="me").execute()
        for l in results.get("labels", []):
            if l["name"] == label_name:
                return l["id"]


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

    label_id = create_label(gmail_service, "YeHooo")
    print(f"That new/ Label Id: {label_id}")

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
        if result[0] == 0:
            continue

        modify(gmail_service, msg["id"], label_id)

        print(fintext[0])
        print("Label: ", result, "\n\n")

    gmail_service.close()


main()
