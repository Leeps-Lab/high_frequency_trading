
sudo systemctl start high_frequency_trading.service 
sudo journalctl -u high_frequency_trading.service -f > log_hft.txt


sudo systemctl start exchange_server.service
sudo journalctl -u exchange_server.service -f > log_exchange_server.txt

sudo systemctl start exchange_server_fba.service
sudo journalctl -u exchange_server_fba.service -f > log_exchange_server_fba.txt


sudo systemctl start huey_hft.service 
sudo journalctl -u huey_hft.service -f > log_huey_hft.txt




