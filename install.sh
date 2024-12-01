sudo apt-get update -y && sudo apt-get install -y python3 python3-dev build-essential libssl-dev libffi-dev python3-venv python3-pip libpq-dev  
python3 -m venv venv 
source ./venv/bin/activate
sudo apt-get install -y python3-psycopg2
apt-get install -y build-essential
apt-get install -y libpq-dev python3-dev
pip3 install -r requirements.txt
