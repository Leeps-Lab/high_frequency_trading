General
=============

This repo contains an `oTree`_ application customized for conducting real-time financial
market experiments. It originally started as an attempt to build an pure oTree implementation
of the experiment in [Aldrich&LopezVargas]_. It now can support a large set of financial market
environments. 

The general architecture of this experiment software includes of supports the operation of a remote
exchanges (market engine) and human participants operating as traders via an oTree layer. 

In this paradigm, each oTree subsession corresponds to a trading day and one webpage
where subjects participate in a market by interacting with the components on the user interface in real time.

This architecture is capable of creating experimental environments where to study algorithmic and high-frequency trading.

Setting Up
=============

Redis is used as the primary data storage during a trade session for quick read/writes,
and experiment data is written to the Postgres in background.

We use Huey for this purpose. Both Redis and Huey are already required for oTree.
The `interface server`_ is used to connect to remote exchanges.

To run a test:

1. Create a virtual environment, you will install a slightly modified 
version of oTree in this new environment. A virtual environment will keep this version 
separate from the oTree version you are already using.

::

    mkdir otree_hft_env
    virtualenv -p python3.6 otree_hft_env

For mac and linux:

::

    source otree_hft_env/bin/activate

For windows: 

::

    otree_hft_env/Scripts/activate
    
2. Clone this repository and install dependencies.

::  

    cd high_frequency_trading
    pip install -r requirements.txt

3. For convenience the repository includes matching engine libraries as subrepo. Some modules
are used by both the exchange server and application. Both applications decode/encode
`OUCH`_ messages to talk with each other. 

::

    cd exchange_server
    git submodule init 
    git submodule update 

Follow the `exchange server instructions`_ and run a CDA exchange instance.

4. Postgres DB and Redis must be running and oTree must be configured to talk 
with both; explained in `oTree docs`_ . Also run:

::

    otree resetdb
    otree collectstatic

5. In a separate shell start the background process.
   
::

     otree run_huey

6. Finally, run oTree in another shell.

::

    otree runhftserver

In production, you should run each as a service. The method above
is only intended for testing.


.. _oTree: http://www.otree.org/
.. [Aldrich&LopezVargas] https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3154070
.. _interface server: https://github.com/django/daphne
.. _OUCH: http://www.nasdaqtrader.com/content/technicalsupport/specifications/tradingproducts/ouch4.2.pdf
.. _exchange server instructions: https://github.com/Leeps-Lab/exchange_server/blob/4cf00614917e792957579ecdd0f5719f9780b94c/README.rst
.. _oTree docs: https://otree.readthedocs.io/en/latest/server/intro.html
