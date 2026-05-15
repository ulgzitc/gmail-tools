import os
import time
import pprint
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

pp = pprint.PrettyPrinter(indent=2)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def mark_as_read(service, messages):
    msg_ids = [msg["id"] for msg in messages]
    print("Labeling the emails...")

    i = 0
    rank = 999
    num_iter = len(msg_ids) // rank + 1
    while i < num_iter:
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


def read(token_path, creds_path, port):
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
            "Token saved to:",
            path,
            "\n"
            "You can use the token next time [-t path/to/token.json], but expires at ~1 hour.",
        )

    else:
        print(
            "Credentials are not given. Please use -c path/to/creds.json or -t path/to/token.json"
        )
        return
    gmail_service = build("gmail", "v1", credentials=creds)

    messages_to_unread = query_messages(
        service=gmail_service, qfilter="is:unread")
    if len(messages_to_unread) == 0:
        print("There's nothing to unread.")
        gmail_service.close()
        return
    mark_as_read(gmail_service, messages_to_unread)
    runtime = time.time() - start
    print("Finished.")
    print(f"Total runtime: {runtime:.2f} seconds. a.k.a ~{
          (runtime / 60):.2f} minutes.")

    gmail_service.close()
