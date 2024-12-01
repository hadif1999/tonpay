sudo apt-get update -y
sudo apt-get install -y python3
python3 -m venv venv 
source ./venv/bin/activate
sudo apt-get install -y build-essential libssl-dev libffi-dev
sudo apt-get -y install libpq-dev python3-dev
pip3 install -U setuptools wheel pip
sudo apt-get install -y python3-psycopg2
pip3 install -r requirements.txt
