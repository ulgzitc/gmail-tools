import re
import base64


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

        good_messages.append({"messages": message, "labels": labels, "label": label})
    return good_messages
