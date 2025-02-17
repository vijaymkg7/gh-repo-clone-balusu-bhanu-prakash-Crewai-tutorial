import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import ollama
import streamlit as st

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
ollama_client = ollama.Client('http://localhost:11434')

def authenticate_gmail():
    creds = None
    st.title("📧 Google API Authentication")
    client_id = st.text_input("Enter Client ID", type="password")
    client_secret = st.text_input("Enter Client Secret", type="password")
    project_id = st.text_input("Enter Project ID", help="Find this in Google Cloud Console > Project Settings")

    if st.button("Authenticate"):
        credentials_data = {
            "installed": {
                "client_id": client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"]
            }
        }
        with open('credentials.json', 'w') as f:
            import json
            json.dump(credentials_data, f)

        try:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            st.success("Authentication successful!")
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
    return creds

def main():
    st.title("📧 AI-Powered Gmail Organizer")
    creds = authenticate_gmail()
    if creds:
        service = build('gmail', 'v1', credentials=creds)
        st.success("Gmail API connected successfully")
        st.write("Now you can organize your emails using AI.")

if __name__ == '__main__':
    main()
