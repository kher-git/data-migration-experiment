🛠️ AWS → OCI Data Migration Tool

This project lets you migrate files from AWS S3 to Oracle Cloud Infrastructure (OCI) Object Storage.

You can run it in two ways:

🐍 Local (Python CLI) – interactive and beginner-friendly.

🐳 OCI Container Instance – automated, non-interactive execution in the cloud.

Both methods use the same process: download → compress → upload.
The main difference is how credentials and configuration are provided.

⚙️ Shared Prerequisites (for both methods)

Before starting, ensure you have the following:

✅ Accounts & Buckets

AWS account with an existing S3 bucket.

OCI account with an Object Storage bucket.

OCI user with API keys (generate one if you haven’t yet).

🔑 Credentials Required
Service	Credential	Purpose
AWS	Access Key ID & Secret Access Key	Authenticate S3 access
OCI	Tenancy OCID, User OCID, Fingerprint, Region, API Key (.pem)	Authenticate uploads to Object Storage
🌍 OPTION 1 — Local Interactive Method (migrate_prompts.py)

This method runs locally (your computer or Cloud Shell) and prompts you for details interactively.
It’s best for learning or running a one-time migration.

🧰 Step 1 — Clone the Repository
git clone https://github.com/your-username/data-migration-experiment.git
cd data-migration-experiment

🐍 Step 2 — Set Up Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

🔐 Step 3 — Configure AWS and OCI

AWS

aws configure --profile my_profile


OCI

oci setup config


After running the OCI setup, upload the generated public key file in the OCI Console:
Profile → API Keys → Add API Key

▶️ Step 4 — Run the Script
python migrate_prompts.py


You’ll be asked to provide:

AWS profile or environment credentials

AWS region, bucket name, and optional prefix

OCI profile and bucket name

Local download folder and archive name

Once complete:

✅ Data migration completed successfully.

☁️ OPTION 2 — OCI Container Instance Method (migrate.py)

This method runs the migration automatically within OCI.
It does not require prompts — instead, it uses environment variables.

⚙️ Step 1 — Prepare OCI Access
1️⃣ Create a Dynamic Group

Navigate to Identity & Security → Dynamic Groups → Create Dynamic Group
Rule example:

ALL {resource.type = 'containerinstance', resource.compartment.id = '<your-compartment-ocid>'}

2️⃣ Create a Policy

Go to Identity & Security → Policies → Create Policy
Policy example:

Allow dynamic-group <your-dg-name> to manage objects in compartment <your-compartment-name>

🔑 Step 2 — Set Environment Variables

Replace all placeholders with your own values:

# OCI Details
export COMPARTMENT_ID="<your-compartment-ocid>"
export SUBNET_ID="<your-public-subnet-ocid>"
export AD_NAME="$(oci iam availability-domain list --compartment-id $COMPARTMENT_ID --query 'data[0].name' --raw-output)"
export CI_NAME="dme-ci-test"

# AWS Info
export AWS_ACCESS_KEY_ID="<your-aws-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-aws-secret-key>"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_BUCKET_NAME="<your-s3-bucket>"
export AWS_PREFIX=""

# OCI Bucket
export OCI_BUCKET_NAME="<your-oci-bucket>"


💡 Tip: You can save these in a .env file and load them later with:

source .env

📁 Step 3 — Create the Configuration Files

vnics.json

cat > vnics.json <<EOF
[
  {
    "subnetId": "$SUBNET_ID",
    "assignPublicIp": "true"
  }
]
EOF


containers.json

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
oci container-instances container-instance create \
  --compartment-id $COMPARTMENT_ID \
  --availability-domain "$AD_NAME" \
  --display-name $CI_NAME \
  --shape "CI.Standard.A1.Flex" \
  --shape-config '{"ocpus":1,"memoryInGBs":1}' \
  --vnics file://vnics.json \
  --containers file://containers.json


The response will show "lifecycle-state": "CREATING".
Wait until it changes to "ACTIVE".

🔍 Step 5 — Verify the Migration
oci os object list -bn $OCI_BUCKET_NAME --query "data[].name" --raw-output


Expected:

aws_archive.tar.xz

🧹 Step 6 — Clean Up
oci container-instances container-instance delete \
  --container-instance-id <your-ci-ocid> --force

🧠 Notes & Tips

migrate_prompts.py → Interactive prompts (local or Cloud Shell)

migrate.py → Environment-based automation (OCI container)

Log uploads are optional; missing logs won’t affect migration results.

Uses .tar.xz compression for smaller transfer size.

Tested with OCI CLI v3.67+ and Python SDK 2.160.3+.

🧾 License

MIT License — You’re free to use, modify, and share this tool with credit.
