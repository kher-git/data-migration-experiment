# 🛠️ AWS → OCI Data Migration Tool

This project lets you **migrate files from AWS S3 to Oracle Cloud Infrastructure (OCI) Object Storage**.

You can run it in **two ways**:

1. 🐍 **Local (Python CLI)** – interactive and beginner-friendly.  
2. 🐳 **OCI Container Instance** – automated, non-interactive execution in the cloud.

Both methods use the same logic — download → compress → upload — but differ in setup and authentication.

---

## ⚙️ Shared Prerequisites (for both methods)

Before running either version, you’ll need:

### ✅ Accounts & Buckets
- **AWS account** with an S3 bucket containing readable files.  
- **OCI account** with an Object Storage bucket created.  
- **OCI user with API keys** (generate one if needed).

### 🔑 Credentials Required

| Service | Credential | Purpose |
|----------|-------------|----------|
| AWS | Access Key ID & Secret Access Key | Authenticate S3 access |
| OCI | Tenancy OCID, User OCID, Fingerprint, Region, API Key (.pem) | Authenticate Object Storage |

---

## 🌍 OPTION 1 — Local Interactive Method (`migrate_prompts.py`)

This version runs **locally** (your computer or Cloud Shell) and **prompts you** for details.  
Best for manual testing or learning.

---

### 🧰 Step 1 — Clone the Repository
```bash
git clone https://github.com/your-username/data-migration-experiment.git
cd data-migration-experiment
🐍 Step 2 — Set Up Python
bash
Copy code
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
🔐 Step 3 — Configure AWS and OCI
AWS

bash
Copy code
aws configure --profile my_profile
OCI

bash
Copy code
oci setup config
Upload the public key in the OCI Console under
Profile → API Keys → Add API Key

▶️ Step 4 — Run the Script
bash
Copy code
python migrate_prompts.py
The script will ask for:

AWS profile or environment credentials

AWS region & bucket

OCI profile & bucket

Local download folder and archive name

Success message:

Copy code
✅ Data migration completed successfully.
☁️ OPTION 2 — OCI Container Instance (migrate.py)
This version runs automatically inside OCI without prompts.
Instead, it reads environment variables you define.

⚙️ Step 1 — Prepare OCI Access
1️⃣ Create a Dynamic Group
Console → Identity & Security → Dynamic Groups → Create Dynamic Group

python
Copy code
ALL {resource.type = 'containerinstance', resource.compartment.id = '<your-compartment-ocid>'}
2️⃣ Create a Policy
Console → Identity & Security → Policies → Create Policy

pgsql
Copy code
Allow dynamic-group <your-dg-name> to manage objects in compartment <your-compartment-name>
🔑 Step 2 — Set Environment Variables
Run these in Cloud Shell (replace placeholders):

bash
Copy code
# OCI
export COMPARTMENT_ID="<your-compartment-ocid>"
export SUBNET_ID="<your-public-subnet-ocid>"
export AD_NAME="$(oci iam availability-domain list --compartment-id $COMPARTMENT_ID --query 'data[0].name' --raw-output)"
export CI_NAME="dme-ci-test"

# AWS
export AWS_ACCESS_KEY_ID="<your-aws-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-aws-secret-key>"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_BUCKET_NAME="<your-s3-bucket>"
export AWS_PREFIX=""

# OCI Bucket
export OCI_BUCKET_NAME="<your-oci-bucket>"
💡 Tip: Save these to a .env file to re-use later.

📁 Step 3 — Create Configuration Files
vnics.json

bash
Copy code
cat > vnics.json <<EOF
[
  {
    "subnetId": "$SUBNET_ID",
    "assignPublicIp": "true"
  }
]
EOF
containers.json

bash
Copy code
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
🚀 Step 4 — Deploy the Container Instance
bash
Copy code
oci container-instances container-instance create \
  --compartment-id $COMPARTMENT_ID \
  --availability-domain "$AD_NAME" \
  --display-name $CI_NAME \
  --shape "CI.Standard.A1.Flex" \
  --shape-config '{"ocpus":1,"memoryInGBs":1}' \
  --vnics file://vnics.json \
  --containers file://containers.json
Wait until "lifecycle-state": "ACTIVE" appears.

🔍 Step 5 — Verify Your Migration
bash
Copy code
oci os object list -bn $OCI_BUCKET_NAME --query "data[].name" --raw-output
Expected output:

Copy code
aws_archive.tar.xz
That confirms the transfer succeeded.

🧹 Step 6 — Clean Up
bash
Copy code
oci container-instances container-instance delete \
  --container-instance-id <your-ci-ocid> --force
🧠 Notes & Tips
migrate_prompts.py = interactive (local)

migrate.py = non-interactive (container)

Log uploads are optional — their absence does not affect migration.

Uses .tar.xz compression for smaller transfers.

Tested on OCI CLI v3.67+ and Python SDK 2.160.3+.
