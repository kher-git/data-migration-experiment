import boto3
import oci
import os
import tarfile
import sys
from datetime import datetime

# -------------------------------
# USER CONFIGURATION SECTION
# -------------------------------

# AWS Configuration
AWS_PROFILE = "my_profile"                  # Profile from ~/.aws/credentials
AWS_BUCKET_NAME = "disbatch"            # Your AWS S3 bucket name
AWS_REGION = "us-east-1"                # Your AWS region

# OCI Configuration
OCI_CONFIG_FILE = os.path.expanduser("~/.oci/config")  # Path to your OCI config file
OCI_PROFILE = "DEFAULT"                 # Profile name inside your OCI config file
OCI_BUCKET_NAME = "DataMigration_BKT"   # Destination bucket name in OCI
OCI_NAMESPACE = None                    # We'll fetch this automatically

# Migration Settings
LOCAL_DOWNLOAD_DIR = "/tmp/aws_migration"     # Where S3 files will be stored
ARCHIVE_NAME = "aws_archive.tar.xz"           # Name of the compressed file
COMPRESSED_PATH = f"/tmp/{ARCHIVE_NAME}"      # Full path to compressed archive
AWS_PREFIX = ""                               # If you want to limit to a folder/prefix in S3


# -------------------------------
# FUNCTIONS
# -------------------------------

def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def download_from_s3():
    log("Setting up AWS S3 session...")
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3 = session.client("s3", region_name=AWS_REGION)

    if not os.path.exists(LOCAL_DOWNLOAD_DIR):
        os.makedirs(LOCAL_DOWNLOAD_DIR)

    log(f"Listing objects in S3 bucket '{AWS_BUCKET_NAME}' with prefix '{AWS_PREFIX}'...")
    objects = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, Prefix=AWS_PREFIX)

    if "Contents" not in objects:
        log("No files found in S3.")
        return

    for obj in objects["Contents"]:
        key = obj["Key"]
        local_path = os.path.join(LOCAL_DOWNLOAD_DIR, os.path.basename(key))

        log(f"Downloading {key} to {local_path}...")
        s3.download_file(AWS_BUCKET_NAME, key, local_path)

    log("All files downloaded from S3.")

def compress_files():
    log(f"Compressing files into {COMPRESSED_PATH}...")

    with tarfile.open(COMPRESSED_PATH, "w:xz") as tar:
        tar.add(LOCAL_DOWNLOAD_DIR, arcname=".")

    log("Compression complete.")

def upload_to_oci():
    log("Setting up OCI client...")
    config = oci.config.from_file(OCI_CONFIG_FILE, OCI_PROFILE)
    client = oci.object_storage.ObjectStorageClient(config)

    global OCI_NAMESPACE
    OCI_NAMESPACE = client.get_namespace().data

    filename = os.path.basename(COMPRESSED_PATH)
    log(f"Uploading {filename} to OCI bucket '{OCI_BUCKET_NAME}'...")

    with open(COMPRESSED_PATH, "rb") as f:
        client.put_object(
            OCI_NAMESPACE,
            OCI_BUCKET_NAME,
            filename,
            f
        )

    log("Upload to OCI complete.")

# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    try:
        download_from_s3()
        compress_files()
        upload_to_oci()
        log("✅ Data migration completed successfully.")
    except Exception as e:
        log(f"❌ Error occurred: {e}")
        sys.exit(1)

