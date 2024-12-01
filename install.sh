sudo apt-get update -y && sudo apt-get install -y python3 python3-dev build-essential libssl-dev libffi-dev python3-venv python3-pip libpd-dev
python3 -m venv venv 
source ./venv/bin/activate
pip3 install -U setuptools wheel pip
sudo apt-get install -y python3-psycopg2
pip3 install -r requirements.txt
