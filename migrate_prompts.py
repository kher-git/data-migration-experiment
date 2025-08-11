import boto3
import oci
import os
import tarfile
import sys
from datetime import datetime

# -------------------------------
# FUNCTIONS
# -------------------------------

def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def prompt_user():
    log("🔧 Starting interactive configuration...")

    aws_profile = input("Enter AWS CLI profile [default]: ") or "default"
    aws_region = input("Enter AWS region [us-east-1]: ") or "us-east-1"
    aws_bucket = input("Enter AWS S3 bucket name: ").strip()
    aws_prefix = input("Enter optional S3 folder/prefix (leave blank for full bucket): ").strip()

    oci_profile = input("Enter OCI profile name [DEFAULT]: ") or "DEFAULT"
    oci_bucket = input("Enter OCI bucket name: ").strip()

    local_download_dir = input("Local download folder [/tmp/aws_migration]: ").strip() or "/tmp/aws_migration"
    archive_name = input("Compressed archive name [aws_archive.tar.xz]: ").strip() or "aws_archive.tar.xz"
    compressed_path = os.path.join("/tmp", archive_name)

    return {
        "aws_profile": aws_profile,
        "aws_region": aws_region,
        "aws_bucket": aws_bucket,
        "aws_prefix": aws_prefix,
        "oci_profile": oci_profile,
        "oci_bucket": oci_bucket,
        "local_download_dir": local_download_dir,
        "archive_name": archive_name,
        "compressed_path": compressed_path
    }

def download_from_s3(config):
    log("Setting up AWS S3 session...")
    session = boto3.Session(profile_name=config["aws_profile"])
    s3 = session.client("s3", region_name=config["aws_region"])

    if not os.path.exists(config["local_download_dir"]):
        os.makedirs(config["local_download_dir"])

    log(f"Listing objects in S3 bucket '{config['aws_bucket']}' with prefix '{config['aws_prefix']}'...")
    objects = s3.list_objects_v2(Bucket=config["aws_bucket"], Prefix=config["aws_prefix"])

    if "Contents" not in objects:
        log("No files found in S3.")
        return

    for obj in objects["Contents"]:
        key = obj["Key"]
        local_path = os.path.join(config["local_download_dir"], os.path.basename(key))

        log(f"Downloading {key} to {local_path}...")
        s3.download_file(config["aws_bucket"], key, local_path)

    log("All files downloaded from S3.")

def compress_files(config):
    log(f"Compressing files into {config['compressed_path']}...")

    with tarfile.open(config["compressed_path"], "w:xz") as tar:
        tar.add(config["local_download_dir"], arcname=".")

    log("Compression complete.")

def upload_to_oci(config):
    log("Setting up OCI client...")
    oci_config = oci.config.from_file("~/.oci/config", config["oci_profile"])
    client = oci.object_storage.ObjectStorageClient(oci_config)

    namespace = client.get_namespace().data
    filename = os.path.basename(config["compressed_path"])

    log(f"Uploading {filename} to OCI bucket '{config['oci_bucket']}'...")
    with open(config["compressed_path"], "rb") as f:
        client.put_object(namespace, config["oci_bucket"], filename, f)

    log("Upload to OCI complete.")

# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    try:
        config = prompt_user()
        download_from_s3(config)
        compress_files(config)
        upload_to_oci(config)
        log("✅ Data migration completed successfully.")
    except Exception as e:
        log(f"❌ Error occurred: {e}")
        sys.exit(1)

