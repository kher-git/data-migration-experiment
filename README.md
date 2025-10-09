# 🛠️ AWS → OCI Data Migration Tool

This project helps you migrate files from **AWS S3** to **Oracle Cloud Infrastructure (OCI) Object Storage**.

You can run it in two ways:
1. 🐍 **Local (Python CLI)** — interactive and beginner-friendly  
2. 🐳 **OCI Container Instance** — automated and non-interactive in the cloud  

Both methods follow the same process: **download → compress → upload**.  
The difference is **how credentials are provided**.

---

## ⚙️ Shared Prerequisites (for both methods)

### ✅ Accounts & Buckets
- AWS account with an existing **S3 bucket**
- OCI account with an **Object Storage bucket**
- OCI user with an **API key pair (`.pem`)**

### 🔑 Credentials Required

| Service | Credential | Purpose |
|----------|-------------|----------|
| **AWS** | Access Key ID + Secret Access Key | Authenticate S3 access |
| **OCI** | Tenancy OCID, User OCID, Fingerprint, Region, API Key (.pem) | Authenticate Object Storage |

### IMPORTANT NOTES
- Carefully review the code as you input and replace all placeholders of **<value>** with your actual information
- **migrate_prompts.py** → interactive version for Cloud Shell or local testing
- **migrate.py** → environment-based automation for OCI container instances
- Log uploads are optional; missing logs won’t affect successful transfers
- Uses .tar.xz compression for efficient upload to Object Storage
- Tested with OCI CLI v3.67+ and Oracle Python SDK v2.160.3+

---

## 🌍 OPTION 1 — Local Interactive Method - migrate_prompts.py

This method runs locally (or in Cloud Shell) and prompts you for details interactively.  
It’s best for learning or running a one-time migration.
Ensure you are using the script **migrate_prompts.py** for this method

---

### 🧰 Step 1 — Clone the Repository

Download the project from GitHub so you can run the script locally.
```bash
git clone https://github.com/<your-username>/data-migration-experiment.git
cd data-migration-experiment
```

What’s happening:
- The git clone command copies the entire repository (code, README, and dependencies).
- cd moves you into that new project directory so later commands work in the correct context.

---

### 🐍 Step 2 — Set Up Python

Create a Python virtual environment and install all required packages.
```bash
python3 -m venv venv
source venv/bin/activate #On Windows: source venv\Scripts\activate
pip install -r requirements.txt
```

What’s happening:
- python3 -m venv venv makes an isolated environment named venv so your global Python packages stay untouched.
- source venv/bin/activate switches your terminal into that environment (you’ll see (venv) appear).
- pip install -r requirements.txt installs the SDKs and libraries:
  - boto3 → AWS SDK for Python
  - oci → Oracle Cloud Infrastructure SDK
  - tarfile and others for compression

---

### 🔐 Step 3 — Configure AWS and OCI

Both clouds need credentials for secure access.

🟠 AWS Credentials

Run this to create your AWS CLI config:
```bash
aws configure --profile my_profile
```

Here You’ll be prompted for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g. us-east-1)
- Output format (json recommended)

🔵 OCI Credentials

Generate your OCI CLI configuration:
```bash
oci setup config
```

Next, upload the public key file in the OCI Console:
Profile → API Keys → Add API Key

Example snippet of ~/.oci/config:
```bash
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=aa:bb:cc:dd:ee:ff
key_file=/Users/you/.oci/api_key.pem
tenancy=ocid1.tenancy.oc1..aaaa...
region=us-ashburn-1
```

---

### ▶️ Step 4 — Run the Script
Start the migration interactively:
```bash
python migrate_prompts.py
```

You’ll be prompted for the following:

| **Prompt** | **Description / Example** |
|-------------|----------------------------|
| **AWS CLI profile (optional)** | If configured, enter your profile name (e.g., `my_profile`). Press **Enter** to use default environment credentials. |
| **AWS region** | Your AWS region, such as `us-east-1` or `eu-west-1`. |
| **AWS S3 bucket name** | The source bucket that contains the data you want to migrate. |
| **S3 folder/prefix (optional)** | A subfolder path within your S3 bucket. Leave blank to migrate everything. |
| **OCI profile name** | Usually `DEFAULT`. Leave blank if running in OCI with resource principals. |
| **OCI bucket name** | The target bucket in Oracle Object Storage where files will be uploaded. |
| **Local download folder** | Temporary directory for downloaded files. Defaults to `/tmp/aws_migration`. |
| **Archive name** | The compressed file name that will be uploaded. Defaults to `aws_archive.tar.xz`. |

🧪 Expected Output

Once started, you’ll see real-time logs similar to this:
```bash
[15:54:40] 🔧 Starting interactive configuration...
[15:54:45] Setting up AWS S3 session...
[15:54:46] Listing objects in S3 bucket 'my-data-bucket' with prefix ''...
[15:54:52] Downloaded 8 files to /tmp/aws_migration
[15:54:52] Compressing files into /tmp/aws_archive.tar.xz...
[15:54:53] Compression complete (42 MB → 6 MB)
[15:54:53] Setting up OCI client...
[15:54:54] Uploading aws_archive.tar.xz to OCI bucket 'my-oci-bucket'...
[15:54:58] ✅ Upload complete. Data migration successful!
```

What’s happening:
1. Downloads objects from your specified S3 bucket.
2. Compresses the files locally into a single .tar.xz archive for efficiency.
3. Uploads that archive to your OCI Object Storage bucket.
   - If successful, the file appears in your OCI bucket.

You can verify by running:
```bash
oci os object list -bn <your-oci-bucket> --query "data[].name" --raw-output
# Expected output:
aws_archive.tar.xz
# If you see this file, your migration ran successfully inside OCI.
```

---

## ☁️ OPTION 2 — OCI Container Instance Method (migrate.py)

This method runs automatically inside OCI using environment variables.
It’s ideal for repeatable or scheduled migrations.

### ⚙️ Step 1 — Prepare OCI Access
1️⃣ Create a Dynamic Group

In OCI Console:
Identity & Security → Dynamic Groups → Create Dynamic Group

Example rule:
```plsql
ALL {resource.type = 'containerinstance', resource.compartment.id = '<your-compartment-ocid>'}
```

2️⃣ Create a Policy

In OCI Console:
Identity & Security → Policies → Create Policy

Example:
```plsql
Allow dynamic-group <your-dg-name> to manage objects in compartment <your-compartment-name>
```

---

### 🔑 Step 2 — Set Environment Variables

```bash
# OCI Details
export COMPARTMENT_ID="<your-compartment-ocid>"
export SUBNET_ID="<your-public-subnet-ocid>"
export AD_NAME="$(oci iam availability-domain list --compartment-id $COMPARTMENT_ID --query 'data[0].name' --raw-output)"
export CI_NAME="dme-ci-instance"
export OCI_BUCKET_NAME="<your-oci-bucket>"
```
```bash
# AWS Details
export AWS_ACCESS_KEY_ID="<your-aws-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-aws-secret-key>"
export AWS_DEFAULT_REGION="<your-aws-region>"
export AWS_BUCKET_NAME="<your-s3-bucket>"
export AWS_PREFIX=""
```

💡 **Optional Tip:** 
You can save these variables into a file and load them later using with **source .env**:
By default, environment variables you `export` only last until you close the terminal.
To avoid re-entering them every time, you can create a **`.env` file** that stores your credentials safely and loads them automatically later.

```bash
# Create a `.env` file
cat > .env <<EOF
export AWS_ACCESS_KEY_ID="<your-aws-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-aws-secret-key>"
export AWS_DEFAULT_REGION="<your-aws-region>"
export AWS_BUCKET_NAME="<your-s3-bucket>"
export AWS_PREFIX=""
export OCI_BUCKET_NAME="<your-oci-bucket>"
export COMPARTMENT_ID="<your-compartment-ocid>"
export SUBNET_ID="<your-subnet-ocid>"
export AD_NAME="$(oci iam availability-domain list --compartment-id $COMPARTMENT_ID --query 'data[0].name' --raw-output)"
export CI_NAME="dme-ci-instance"
EOF
```

---

### 📁 Step 3 — Create Configuration Files

You’ll now create two configuration files (`vnics.json` and `containers.json`) that define how the container instance connects to your OCI network and runs your image.

### 🧩 vnics.json
```bash
cat > vnics.json <<EOF
[
  {
    "subnetId": "$SUBNET_ID",
    "assignPublicIp": "true"
  }
]
EOF
```

### 🐳 containers.json
```bash
cat > containers.json <<EOF
[
  {
    "imageUrl": "ghcr.io/your-username/data-migration-experiment:latest",
    "command": ["python", "migrate.py"],
    "environmentVariables": {
      "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
      "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
      "AWS_DEFAULT_REGION": "$AWS_DEFAULT_REGION",
      "AWS_BUCKET_NAME": "$AWS_BUCKET_NAME",
      "AWS_PREFIX": "$AWS_PREFIX",
      "OCI_BUCKET_NAME": "$OCI_BUCKET_NAME",
      "LOCAL_DOWNLOAD_DIR": "/tmp/aws_migration",
      "ARCHIVE_NAME": "aws_archive.tar.xz"
    }
  }
]
EOF
```

---

### 🚀 Step 4 — Deploy the Container Instance

Run the following command to deploy your container in OCI.
Replace <your-shape> with any available container shape (e.g. CI.Standard.A1.Flex).
If you need a just need a small shape that works with a quota limit, use **CI.Standard.A1.Flex**.

```bash
oci container-instances container-instance create \
  --compartment-id $COMPARTMENT_ID \
  --availability-domain "$AD_NAME" \
  --display-name $CI_NAME \
  --shape "<your-shape>" \
  --shape-config '{"ocpus":1,"memoryInGBs":1}' \
  --vnics file://vnics.json \
  --containers file://containers.json
```

The response will include:
```json
"lifecycle-state": "CREATING"
```
Wait until the lifecycle state changes to:
```json
"lifecycle-state": "ACTIVE"
```

---

### 🔍 Step 5 — Verify the Migration

List the objects in your OCI bucket to confirm the migration was successful.
```bash
oci os object list -bn $OCI_BUCKET_NAME --query "data[].name" --raw-output
# Expected Output
aws_archive.tar.xz
# If you see this file, your migration ran successfully inside OCI.
```

---

### 🧹 Step 6 — Clean Up

Once testing is complete, you can delete your container instance to avoid extra cost.
```bash
oci container-instances container-instance delete \
  --container-instance-id <your-ci-ocid> --force
```

---

### 🧾 License

MIT License – You’re free to use, modify, and share this tool with credit.
