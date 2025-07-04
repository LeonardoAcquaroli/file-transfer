import streamlit as st
import os
import time
import json
from google.cloud import storage
from google.oauth2 import service_account
import pandas as pd
from io import BytesIO

if os.path.exists(".env"):
    st.write("Loading environment variables from local .env file")
    import dotenv
    dotenv.load_dotenv()

# Read environment variables set via GitHub Codespaces secrets
BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME")
FOLDER_NAME = os.environ.get("GCP_FOLDER_NAME")

def get_storage_client():
    credentials_info = os.environ.get("GCP_CREDENTIALS")
    if not credentials_info:
        st.error("GCP_CREDENTIALS not found in environment variables.")
        st.stop()
    credentials_info = json.loads(credentials_info)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    return storage.Client(credentials=credentials)

def list_files(bucket_name, folder_name):
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_name)
    files = []
    for blob in blobs:
        if not blob.name.endswith("/"):
            files.append({
                "Name": blob.name,
                "Size (KB)": round(blob.size / 1024, 2) if blob.size else 0,
                "Last Modified": blob.updated.strftime('%Y-%m-%d %H:%M:%S') if blob.updated else "-"
            })
    return files

def upload_file(bucket_name, folder_name, file):
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(folder_name + file.name)
    blob.upload_from_file(file)
    return True

def delete_file(bucket_name, file_path):
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.delete()
    return True

st.title("File Transfer Service")

# List files
st.header("Loaded Files")
try:
    files = list_files(BUCKET_NAME, FOLDER_NAME)
    if files:
        df = pd.DataFrame(files)
        st.table(df)
        for file in files:
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                st.write(file["Name"])
            with col2:
                file_name = file["Name"]
                if st.button("Delete", key=f"delete_{file_name}"):
                    delete_file(BUCKET_NAME, file_name)
                    st.success(f"Deleted {file_name}")
                    st.rerun()
            with col3:
                client = get_storage_client()
                bucket = client.bucket(BUCKET_NAME)
                blob = bucket.blob(file_name)
                file_bytes = blob.download_as_bytes()
                st.download_button(
                    label="Download",
                    data=file_bytes,
                    file_name=file_name.split("/")[-1],
                    mime="application/octet-stream",
                    key=f"download_{file_name}"
                )
    else:
        st.write("No files found.")
except Exception as e:
    st.error(f"Error listing files: {e}")

# Upload file
st.header("Upload a File")

# Session state
if 'file_uploader_key' not in st.session_state:
    st.session_state['file_uploader_key'] = 0
if 'pending_file_bytes' not in st.session_state:
    st.session_state['pending_file_bytes'] = None
if 'pending_file_name' not in st.session_state:
    st.session_state['pending_file_name'] = None
if 'pending_file_type' not in st.session_state:
    st.session_state['pending_file_type'] = None

uploaded_file = st.file_uploader("Choose a file to upload", key=st.session_state['file_uploader_key'])

if uploaded_file is not None:
    existing_files = [f["Name"].split("/")[-1] for f in files]
    if st.session_state['pending_file_name'] != uploaded_file.name:
        st.session_state['pending_file_bytes'] = uploaded_file.getvalue()
        st.session_state['pending_file_name'] = uploaded_file.name
        st.session_state['pending_file_type'] = uploaded_file.type

    if uploaded_file.name in existing_files:
        st.warning(f"A file named '{uploaded_file.name}' already exists in the bucket.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Overwrite", key="overwrite_btn"):
                try:
                    file_to_upload = BytesIO(st.session_state['pending_file_bytes'])
                    file_to_upload.name = st.session_state['pending_file_name']
                    file_to_upload.type = st.session_state['pending_file_type']
                    with st.spinner(f"Uploading {file_to_upload.name} (overwriting)..."):
                        upload_file(BUCKET_NAME, FOLDER_NAME, file_to_upload)
                    st.success(f"Uploaded {file_to_upload.name} (overwritten)")
                except Exception as e:
                    st.error(f"Error uploading file: {e}")
                st.session_state['file_uploader_key'] += 1
                st.session_state['pending_file_bytes'] = None
                st.session_state['pending_file_name'] = None
                st.session_state['pending_file_type'] = None
                time.sleep(1)
                st.rerun()
        with col2:
            if st.button("Cancel Upload", key="cancel_btn"):
                st.info("Upload cancelled.")
                st.session_state['file_uploader_key'] += 1
                st.session_state['pending_file_bytes'] = None
                st.session_state['pending_file_name'] = None
                st.session_state['pending_file_type'] = None
                time.sleep(1)
                st.rerun()
    else:
        try:
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                upload_file(BUCKET_NAME, FOLDER_NAME, uploaded_file)
            st.success(f"Uploaded {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error uploading file: {e}")
        st.session_state['file_uploader_key'] += 1
        st.session_state['pending_file_bytes'] = None
        st.session_state['pending_file_name'] = None
        st.session_state['pending_file_type'] = None
        st.rerun()