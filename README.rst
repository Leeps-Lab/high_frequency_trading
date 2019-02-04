General
=============

This repo contains an `oTree`_ application customized for conducting real-time financial
market experiments. It originally started as an attempt to build an pure oTree implementation
of the experiment in [AldrichAndLopezVargas]_. It now supports a large set of financial market
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

To run a test:

1. Create a virtual environment, you will install a slightly modified 
version of oTree in this new environment. A virtual environment will keep this version 
separate from the oTree version you might be already using.

.. warning::
    If you have a version of oTree installed in your computer and do not use a virtual environment
    to do Step 1, you will overwrite your current oTree installation. 

This assumes that you have Python 3.6 (thus pip3) installed on your computer. 

Make sure to have virtualenv installed by checking the version. 

::

    virtualenv --version

The version for virtualenv should be printed on console, else install virtualenv:

::

    pip3 install virtualenv


Then run:

::

    mkdir otree_hft_env
    virtualenv -p python3.6 otree_hft_env


2. Activate the virtual environment.

For mac and linux:

::

    source otree_hft_env/bin/activate

For windows: 

::

    otree_hft_env/Scripts/activate


3. `Clone`_ this repository, cd into the folder and install dependencies.

::  

    git clone https://github.com/Leeps-Lab/high_frequency_trading.git
    cd high_frequency_trading
    pip3 install -r requirements.txt


4. In a seperate shell, navigate into the folder of the repository you cloned. It is always
a good idea to use a virtual environment. Do step 2, activate the environment previously
created.

::

    cd exchange_server
    git submodule init 
    git submodule update 


Follow the `exchange server instructions`_ and run a CDA exchange instance.

.. note::
    Note: the exchange server has its own repository and, for convenience, this repository 
    includes the exchange server libraries as a subrepo. This is because some modules are used
    by both the exchange server and this application 
    (e.g., both applications decode/encode `OUCH`_ messages o talk with each other).

5. Postgres DB and Redis must be running and oTree must be configured to talk 
with both; explained in `oTree docs`_ .

6. Go back to the shell with new virtual environment, reset the database and copy
static files by running commands below.

::

    otree resetdb
    otree collectstatic


7. Run oTree.

::

    otree runhftserver



8. In a separate shell, activate the new environment and start a background process.

::

     otree run_huey



In summary, there should be 3 processes running in 3 different shells with the new
environment. These will talk to each other during a trade session.

In production, you should run each as a service. The method above
is only intended for testing.


.. _oTree: http://www.otree.org/
.. [AldrichAndLopezVargas] https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3154070
.. _interface server: https://github.com/django/daphne
.. _OUCH: http://www.nasdaqtrader.com/content/technicalsupport/specifications/tradingproducts/ouch4.2.pdf
.. _exchange server instructions: https://github.com/Leeps-Lab/exchange_server/blob/4cf00614917e792957579ecdd0f5719f9780b94c/README.rst
.. _oTree docs: https://otree.readthedocs.io/en/latest/server/intro.html
.. _Clone: https://help.github.com/articles/cloning-a-repository/
.. _guide: https://docs.python-guide.org/dev/virtualenvs/
