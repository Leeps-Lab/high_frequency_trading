
sudo add-apt-repository ppa:deadsnakes/ppa
apt update
apt install -y git postgresql redis-server python3.6 python3.6-venv

sudo -u postgres psql << EOF
CREATE DATABASE django_db;
CREATE USER otree_user WITH PASSWORD 'mydbpassword';
GRANT ALL PRIVILEGES ON DATABASE django_db TO otree_user;
EOF

WORKDIR='/opt'

export DATABASE_URL='postgres://otree_user:mydbpassword@localhost/django_db'

cd $WORKDIR
git clone https://github.com/Leeps-Lab/high_frequency_trading
python3.6 -m venv venv
source venv/bin/activate

cd ./high_frequency_trading
pip install -r requirements.txt
cd ./exchange_server
git submodule init
git submodule update
pip install -r requirements.txt
cd ..
yes | otree resetdb
echo 'yes' | otree collectstatic

cp /vagrant/*.service /etc/systemd/system

systemctl enable otree huey exchange
systemctl start otree huey exchange
