import os
import json
import pprint
import logging
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account


pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger()
logger.setLevel("INFO")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.modify",
]

os.chdir("../../env/")
current_dir = os.getcwd()


def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        f"{current_dir}/client_secret.json", scopes=SCOPES
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=8080,
        authorization_prompt_message="Please visit this URL: {url}",
        success_message="Wahoooo!!!! You can close the window now.",
        open_browser=True,
    )

    gmail_service = build("gmail", "v1", credentials=credentials)
    unread_messages = (
        gmail_service.users().messages().list(userId="me", q="is:unread").execute()
    )
    pp.pprint(unread_messages)

    gmail_service.close()


def main2():
    flow = Flow.from_client_secrets_file(
        f"{current_dir}/client_secret.json",
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )
    auth_uri = flow.authorization_url()
    # Redirect the user to auth_uri on your platform.
    print(auth_uri)
    code = input("Enter the authorization code: ")
    flow.fetch_token(code=code)
    credentials = service_account.Credentials.from_service_account_file(
        f"{current_dir}/client_secret.json"
    )
    scoped_credentials = credentials.with_scopes(
        ["https://www.googleapis.com/auth/gmail.modify"]
    )
