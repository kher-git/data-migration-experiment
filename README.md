Package URL - https://github.com/kher-git/data-migration-experiment/pkgs/container/data-migration-experiment
# Clone the repo
git clone https://github.com/kher-git/data-migration-experiment.git
cd data-migration-experiment

# Create a virtual environment (optional, but recommended)
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the script
python migrate.py
