General
=============

This repo contains an `oTree`_ application customized for conducting real-time financial
market experiments. It originally started as an attempt to build an pure oTree implementation
of the experiment in [Aldrich_LopezVargas]_. It now supports a large set of financial market
environments. 

This application connects to a remote exchange server, and human participants operate
as traders.

In this paradigm, each oTree subsession corresponds to a trading day and one webpage
where subjects participate in a market by interacting with the components on the user interface.

This architecture is inteded for creating experimental environments to study algorithmic 
and high-frequency trading.

Setting Up
=============

Redis is used as the primary data storage during a trade session for quick read/writes,
and experiment data is written to the Postgres in background.

We use Huey for this purpose. Both Redis and Huey are already required for oTree.
The `interface server`_ is used to connect to exchange server.

**Prerequisites**:

The tutorial below assumes that you have Python 3.6 (thus, pip3) installed in your computer as well as an 
up-to-date Google Chrome browser. 

Redis and Postgres databases should be running and oTree configured to talk with them.  See `oTree docs`_ 
documentation for details. 
You can also find instructions to install and run `Redis here`_. 
Similarly, can download and install `Postgres here`_.
We were able to run a couple of successful tests using SQLite (the default development
database for otree) instead of Postgres.


**Step-by-step tutorial to run a simple test**


0. Open four terminals. 


1. Create a virtual environment, you will install a slightly modified 
version of oTree in this new environment. A virtual environment will keep this version 
separate from the oTree version you might be already using.
Warning: If you have a version of oTree installed in your computer and do not use a virtual environment
to do Step 1, you will overwrite your current oTree installation. 

In terminal #1, make sure to have virtualenv installed by checking the version. 

::

    virtualenv --version

The version for virtualenv should be printed on console, else install virtualenv

::

    pip3 install virtualenv

Then run

::

    mkdir otree_hft_env
    virtualenv -p python3.6 otree_hft_env


2. Activate the virtual environment (still in terminal #1).

For mac and linux

::

    source otree_hft_env/bin/activate

For windows 

::

    otree_hft_env/Scripts/activate


3. Using these commands, `clone`_ this repository, cd into the folder and install dependencies (Terminal #1).

::  

    git clone https://github.com/Leeps-Lab/high_frequency_trading.git
    cd high_frequency_trading
    pip3 install -r requirements.txt


4. In Terminal #2, navigate into the folder of the repository you cloned in the previous step. 
Then, using the commands below, cd into the 'exchange_server' folder and download the up-to-date files of the exchange server.

::

    cd exchange_server
    git submodule init 
    git submodule update 

Note: the exchange server has its own repository and, for convenience, this repository 
includes the exchange server libraries as a subrepo. This is because some modules are used
by both the exchange server and this application 
(e.g., both applications decode/encode `OUCH`_ messages o talk with each other).


5. Still in Terminal #2, follow the `exchange server instructions`_ and run a CDA exchange 
instance. 
Expect to see three timestamped lines that look like this:

::

    [14:45:00.803] Using selector: KqueueSelector
    [14:45:00.803] DEBUG [root.__init__:35] Initializing exchange
    [14:45:00.803] INFO [root.register_listener:112] added listener 0


6. Go back to Terminal #1, reset the database and copy static files by running these commands.

::

    otree resetdb
    otree collectstatic


7. Then, in the same Terminal #1, run oTree server.

::

    otree runhftserver

Note: this step requires Redis to be running either in the background or in a separate Terminal (run 'redis-server' in Terminal #4)


8. In Terminal #3, go to the folder that contains 'otree_hft_env' and do Step 2 (activate the virtual environment). 
Then, cd into the 'high_frequency_trading' folder and start the following background process.

::

     cd high_frequency_trading
     otree run_huey


9. Open your Chrome browser and go to `localhost`_. Click on the 'demo session' and follow the screen 
istructions to launch clients' (traders') screens as tabs in the same browser. 


**Final notes**

Here, we have four terminals running four processes that conform to our financial market environment. These processes are talking to each other during a trading session.

In production mode, you should run each of these as a 'service'. The method above is only intended for testing on your personal computer.


.. _oTree: http://www.otree.org/
.. [Aldrich_LopezVargas] https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3154070
.. _interface server: https://github.com/django/daphne
.. _OUCH: http://www.nasdaqtrader.com/content/technicalsupport/specifications/tradingproducts/ouch4.2.pdf
.. _exchange server instructions: https://github.com/Leeps-Lab/exchange_server/blob/4cf00614917e792957579ecdd0f5719f9780b94c/README.rst
.. _oTree docs: https://otree.readthedocs.io/en/latest/server/intro.html
.. _clone: https://help.github.com/articles/cloning-a-repository/
.. _guide: https://docs.python-guide.org/dev/virtualenvs/
.. _Redis here: https://redis.io/download#installation
.. _Postgres here: https://www.postgresql.org/download/
.. _localhost: http://localhost:8000
