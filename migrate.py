import os
import sys
import tarfile
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

import oci
from oci.auth.signers import get_resource_principals_signer

LOG_FILE = "/tmp/migration.log"

def log(msg: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def getenv(key: str, default: str = None) -> str:
    v = os.getenv(key)
    return v if (v is not None and v != "") else default

def require_env(key: str) -> str:
    v = os.getenv(key)
    if v is None or v.strip() == "":
        raise RuntimeError(
            f"Required environment variable '{key}' not set. "
            f"Set it on the Container Instance (or export locally) and re-run."
        )
    return v.strip()

# -------- AWS --------

def setup_s3_client(region: str, profile: str = None):
    log("Setting up AWS S3 session...")
    try:
        if profile:
            log(f"Using AWS profile '{profile}' for authentication.")
            session = boto3.Session(profile_name=profile)
            return session.client("s3", region_name=region)
        else:
            log("Using AWS environment variables for authentication.")
            return boto3.client("s3", region_name=region)
    except NoCredentialsError:
        raise RuntimeError(
            "No AWS credentials found or invalid profile. Either configure ~/.aws or set environment variables."
        )

def download_from_s3(s3, bucket: str, prefix: str, local_dir: str) -> int:
    if not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)

    log(f"Listing objects in S3 bucket '{bucket}' with prefix '{prefix}'...")

    count = 0
    kwargs = {"Bucket": bucket, "Prefix": prefix or "", "MaxKeys": 1000}
    try:
        while True:
            resp = s3.list_objects_v2(**kwargs)
            contents = resp.get("Contents", [])
            if not contents and "NextContinuationToken" not in resp:
                break

            for obj in contents:
                key = obj["Key"]
                if key.endswith("/") and obj.get("Size", 0) == 0:
                    continue
                filename = os.path.basename(key) or "object"
                local_path = os.path.join(local_dir, filename)

                log(f"Downloading s3://{bucket}/{key} -> {local_path} ...")
                s3.download_file(bucket, key, local_path)
                count += 1

            token = resp.get("NextContinuationToken")
            if not token:
                break
            kwargs["ContinuationToken"] = token

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found by boto3 (env vars).")
    except ClientError as e:
        raise RuntimeError(f"AWS S3 error: {e}")

    if count == 0:
        log("No files found in S3 for the given bucket/prefix.")
    else:
        log(f"Downloaded {count} file(s) from S3.")
    return count

# -------- Compression --------

def compress_directory(src_dir: str, archive_name: str) -> str:
    archive_path = os.path.join("/tmp", archive_name)
    log(f"Compressing files into {archive_path}...")
    os.makedirs(src_dir, exist_ok=True)
    with tarfile.open(archive_path, "w:xz") as tar:
        tar.add(src_dir, arcname=".")
    log("Compression complete.")
    return archive_path

# -------- OCI --------

def setup_oci_object_storage_client(oci_profile: str = None, oci_config_file: str = "~/.oci/config"):
    log("Setting up OCI client...")
    try:
        if os.getenv("OCI_RESOURCE_PRINCIPAL_VERSION"):
            log("Using OCI Resource Principals for authentication.")
            signer = get_resource_principals_signer()
            return oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        profile = oci_profile or "DEFAULT"
        cfg = oci.config.from_file(oci_config_file or "~/.oci/config", profile)
        log(f"Using OCI config profile '{profile}'.")
        return oci.object_storage.ObjectStorageClient(cfg)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize OCI Object Storage client: {e}")

def upload_to_oci(object_storage_client, bucket: str, object_name: str, local_path: str) -> None:
    namespace = object_storage_client.get_namespace().data
    log(f"Uploading {os.path.basename(local_path)} to OCI bucket '{bucket}' as '{object_name}'...")
    with open(local_path, "rb") as f:
        object_storage_client.put_object(namespace, bucket, object_name, f)
    log("Upload to OCI complete.")

def try_upload_log(object_storage_client, bucket: str, when_suffix: str) -> None:
    try:
        if not os.path.exists(LOG_FILE):
            return
        namespace = object_storage_client.get_namespace().data
        key = f"logs/migration-{when_suffix}.log"
        with open(LOG_FILE, "rb") as f:
            object_storage_client.put_object(namespace, bucket, key, f)
        log(f"Uploaded run log to '{key}'.")
    except Exception as e:
        log(f"Could not upload migration log file: {e}")

# -------- MAIN (CI) --------

if __name__ == "__main__":
    try:
        require_env("AWS_ACCESS_KEY_ID")
        require_env("AWS_SECRET_ACCESS_KEY")
        aws_region = getenv("AWS_DEFAULT_REGION", "us-east-1")
        aws_bucket = require_env("AWS_BUCKET_NAME")
        aws_prefix = getenv("AWS_PREFIX", "")

        oci_bucket = require_env("OCI_BUCKET_NAME")
        local_download_dir = getenv("LOCAL_DOWNLOAD_DIR", "/tmp/aws_migration")
        archive_name = getenv("ARCHIVE_NAME", "aws_archive.tar.xz")
        oci_object_name = getenv("OCI_OBJECT_NAME", archive_name)
        oci_profile = getenv("OCI_PROFILE", "DEFAULT")
        oci_config_file = getenv("OCI_CONFIG_FILE", "~/.oci/config")
        upload_logs_flag = getenv("UPLOAD_LOGS", "true").lower() in ("1", "true", "yes", "y")

        s3 = setup_s3_client(aws_region)
        download_from_s3(s3, aws_bucket, aws_prefix, local_download_dir)
        archive_path = compress_directory(local_download_dir, archive_name)
        osc = setup_oci_object_storage_client(oci_profile=oci_profile, oci_config_file=oci_config_file)
        upload_to_oci(osc, oci_bucket, oci_object_name, archive_path)

        if upload_logs_flag:
            ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            try_upload_log(osc, oci_bucket, ts)

        log("✅ Data migration completed successfully.")

    except Exception as e:
        log(f"❌ Error occurred: {e}")
        try:
            if "osc" in locals() and "oci_bucket" in locals():
                ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                try_upload_log(osc, oci_bucket, f"failed-{ts}")
        except Exception:
            pass
        sys.exit(1)
