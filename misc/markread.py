import os
import pprint
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

pp = pprint.PrettyPrinter(indent=2)
os.chdir("../../env/")
currend_dir = os.getcwd()

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def mark_as_read(service, messages):
    msg_ids = [msg["id"] for msg in messages]
    print("Length: ", len(msg_ids))

    i = 0
    rank = 999
    num_iter = len(msg_ids) // rank + 1
    while i < num_iter:
        print(f"Iteration: {i}")
        batch = msg_ids[rank * i: rank * (i + 1)]
        service.users().messages().batchModify(
            userId="me",
            body={"ids": batch, "removeLabelIds": ["UNREAD"]},
        ).execute()
        i += 1


def query_messages(service, qfilter):
    messages = []
    result = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=qfilter,
        )
        .execute()
    )
    if "messages" in result:
        messages.extend(result["messages"])
    while "nextPageToken" in result:
        page_token = result["nextPageToken"]
        result = (
            service.users()
            .messages()
            .list(userId="me", q=qfilter, pageToken=page_token)
            .execute()
        )
        if "messages" in result:
            messages.extend(result["messages"])
    return messages


def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    gmail_service = build("gmail", "v1", credentials=creds)

    messages_to_unread = query_messages(
        service=gmail_service, qfilter="is:unread")
    if len(messages_to_unread) == 0:
        print("Messages list is empty.")
        gmail_service.close()
        return
    mark_as_read(gmail_service, messages_to_unread)
    print("Finished.")

    gmail_service.close()


main()
