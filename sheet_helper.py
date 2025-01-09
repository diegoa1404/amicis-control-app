from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "data\credentials.txt"


def get_googlesheet_client():
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(credentials)


def get_googlesheet_client1():
    credentials = Credentials.from_service_account_info( st.secrets["gcp_service_account"] ) 
    client = gspread.authorize(credentials) 
    return client

def load_sheet(sheet_id):
    return get_googlesheet_client().open_by_key(sheet_id)


def download_sheet(sheet_id):
    download_link = f"https://drive.google.com/uc?id={sheet_id}"
    return pd.read_excel(download_link, sheet_name="Base")
