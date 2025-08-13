# AWS to OCI Data Migration Tool 🛠️

This project provides a Python script and containerized solution to **migrate data files from AWS S3 to Oracle Cloud (OCI) Object Storage**.
This tool supports compression and is flexible for both CLI and containerized environments. Follow the instructions below to get started! Please provide comments or feedback. 

---

## 🧰 Features

- 🔐 Secure AWS and OCI CLI authentication
- 📦 Download files from S3, compress them, and upload to OCI
- 🐍 Run natively or as a container via Podman or Docker

---

## 🔧 Prerequisites

Whether running locally or in a container, make sure you have:

- **Valid AWS and OCI credentials**
- **Access to source S3 and destination OCI buckets**
- **Python 3.11+**, if using locally
- **Podman or Docker**, if using containers
    - **Container Package URL** - https://github.com/kher-git/data-migration-experiment/pkgs/container/data-migration-experiment


---

## 📁 Setup Credentials

### 🔑 AWS Credentials
- Run
```
aws configure --profile my_profile
```

Creates: `~/.aws/credentials` & `~/.aws/config`

### 🔐 OCI Credentials
- Run

```
oci setup config
```

Creates: `~/.oci/config` & `~/.oci/api_key.pem`

> If you already have credentials setup, then just ensure that follow the format shown in Step 3 

---

### 🐍 Method 1: Run Locally with Python

Run this project locally if you prefer full code visibility and customization.

#### 🔧 Step 1: Clone the Repository
- Clone the source code to your machine

```
git clone https://github.com/kher-git/data-migration-experiment.git  
cd data-migration-experiment
```

#### 📦 Step 2: Set Up Python Environment
- Make sure you have Python 3.11+ installed

```
python3 -m venv venv  
source venv/bin/activate
    # on Windows: source venv\Scripts\activate  
pip install -r requirements.txt
```

#### 🔐 Step 3: Set Up Your Credentials
- Configure your AWS and OCI credentials to authorize cloud access.  
- These credentials are stored separately but required together for migration to succeed.  

#### AWS (~/.aws/credentials)

```
[my_profile]  
aws_access_key_id = YOUR_AWS_KEY  
aws_secret_access_key = YOUR_AWS_SECRET
```

#### OCI (~/.oci/config)

```
[DEFAULT]  
user=ocid1.user.oc1...  
fingerprint=XX:XX:XX...  
key_file=/Users/yourname/.oci/api-key.pem  
tenancy=ocid1.tenancy...  
region=us-ashburn-1
```

> Ensure your credentials in these files follow their respective formats.
> Ensure your AWS/OCI permissions allow for reading/writing to buckets.

#### ▶️ Step 4: Run the Script
- Run the python script
```
python migrate.py
```

##### 🧪 Example Output

```
[15:54:40] Setting up AWS S3 session...
[15:54:40] Listing objects in S3 bucket 'disbatch' with prefix ''...
[15:54:40] No files found in S3.
[15:54:40] Compressing files into /tmp/aws_archive.tar.xz...
[15:54:40] Compression complete.
[15:54:40] Setting up OCI client...
[15:54:41] Uploading aws_archive.tar.xz to OCI bucket 'DataMigration_BKT'...
[15:54:41] Upload to OCI complete.
[15:54:41] ✅ Data migration completed successfully.
```

---

### 🐳 Method 2: Run in a Container (Podman/Docker)

No Python installation or dependencies needed — just run via container!

#### 🔐 Step 1: Set Up Credentials
- Make sure you have the following files accessible on your local system:

`~/.aws` – AWS credentials (read-only)  
`~/.oci` – OCI config (read-only)

#### ▶️ Step 2: Pull & Run with Podman (or Docker)
- Pull the public container from the Github Container Registry (replace podman with docker, if using Docker)
```
podman pull ghcr.io/kher-git/data-migration-experiment:latest  
```
- Mount your aws credentials and oci configuration to the container for authentication
```
podman run --rm -it \
  -v $HOME/.aws:/root/.aws:ro \
  -v $HOME/.oci:/root/.oci:ro \
  ghcr.io/kher-git/data-migration-experiment:latest  
```

> 💡 These `-v` flags mount your local credentials into the container securely so it can authenticate without hardcoding secrets.

#### ✅ What Happens Inside:
1. Downloads all files from your S3 bucket
2. Compresses them into a `.tar.xz`
3. Uploads that archive to your OCI Object Storage bucket

---

## 📌 Notes on Container Usage

- If pushing the image yourself, use:
```
podman push --format docker ghcr.io/YOUR_USERNAME/YOUR_REPO:latest
```
- You must log in using your **GitHub personal access token (PAT)** when prompted for a password during:
```
podman login ghcr.io
```

---

## 📄 License

MIT License – You’re free to use, modify, and share this tool with credit. Remove or change this license if needed.
