Remember to collect some static files if you are pulling for the first time. Otherwise you will see 500 status while starting up.
This is done by :
```
otree collectstatic
```
To run a matching engine:
```
cd exchange_server
sh run_cda_groups.sh 1
```
Make sure Redis is up and running on default port.
Test this with:
```
redis-cli ping
```
You should get a PONG back.
If you do not have redis installed quick google search will help you to set it up.
This will start a single exchange.
To run the development server:
```
otree runserver
```
