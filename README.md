# chipmunk-finance

Chipmunk Finance is an open-source financial data aggregator. It will connect to your bank websites, and download account information and transactions. Contrary to other similar online services, Chipmunk will store everything locally and no data will leave your computer. Access to the data is protected with a password, and the bank account credentials are encrypted. (Transactions are not currently encrypted in the local database).

Access to different bank websites are implemented as plugins in Python. It is possible for users to add and maintain new web scrapers for banks that are not yet supported. The financial data is fetched directly from the user's bank website, and does not use any third party aggregation system. The data is only stored on the user's computer.

The software currently offers a very basic command-line interface, but a local web-based UI is planned.

This project is just getting started, use at your own risk.

## How to run

Install Chrome Driver for Selenium : https://sites.google.com/a/chromium.org/chromedriver/downloads
MacOS: Place the 'chromedriver' file directly in the /chipmunk folder.


Create and activate Python 3.7 virtual environment, then install modules with:

    pip install -r requirements.txt

Run command line utility:

    python commandline.py

    python commandline.py --user joe --add
    python commandline.py --user joe --update --headless
    python commandline.py --user joe --accounts
    python commandline.py --user joe -t
    python commandline.py --user joe -b
    
