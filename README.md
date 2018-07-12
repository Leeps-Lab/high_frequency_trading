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
This will start a single exchange.
To run the development server:
```
otree runserver
```
