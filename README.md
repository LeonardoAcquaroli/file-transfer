# GCP Storage File Manager (Streamlit)

This Streamlit app allows you to view, upload, and delete files in a specific folder of a Google Cloud Storage bucket.

## Features
- List files in a specified folder of your GCP bucket
- Upload new files to the folder
- Delete files from the folder

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Cloud Credentials:**
   - The app expects a service account key for GCP Storage access.
   - You can provide credentials in one of two ways:
     - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your service account key JSON file.
     - Or, use Streamlit secrets by creating a `.streamlit/secrets.toml` file:
       ```toml
       gcp_bucket_name = "your-bucket-name"
       gcp_folder_name = "your-folder-name/"  # include trailing slash
       gcp_credentials = "<contents of your service account JSON>"
       ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Notes
- Make sure the service account has permissions to list, upload, and delete objects in the specified bucket/folder.
- The folder name should end with a `/` (e.g., `myfolder/`). 