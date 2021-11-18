# dca_binance_investment_bot
A bot that automatically invest using the DCA (Dollar Cost Averaging) strategy

dca_bot contains the relevant code for the bot.
timesync contains the code for the time synchronization (Currently not integrated).


# Steps to configure the bot
## Edit config files in dca_bot/configs
1. (.env) Change .env.example to .env and fill in the API key and secret for the binance API
        
        configs/.env

        BINANCE_KEY=<Binace Api key here>
        BINANCE_SECRET=<Binance Api Secret here>

Get Binance Testnet API keys from: https://testnet.binance.vision/ 

2. (dca_investment_parameter.json) Define the symbols you want to invest in

        [
        {
            // symbol to invest in
            "symbol": "BTCUSDT",                
            
            // amount of quote asset to invest every time
            "investment_amount_quoteasset": 12, 
            
            // time interval (how often to invest): see DCAInvestmentParameter::parse_interval_to_seconds for valid intervals
            "interval": "1d",                   
            
            // time of day to invest, the bot will create the order at the specified time
            "investment_time": "02:00",

            // the start day of the investment, the bot won't start before this date
            "start_date": "2021-11-19"
        },
        // example:
        {
            "symbol": "ETHUSDT",
            "investment_amount_quoteasset": 12,
            "interval": "1w",
            "investment_time": "12:00",
            "start_date": "2021-11-01"
        }
        ]


3. 
Change log options inside config.json to fit your needs. 
A new log file will be created every time at midnight (00:00) and save the old by appending the last timestamp (format: %Y-%m-%d) to it's filename.
e.g. bot.log -> bot.log.2021.11.18

        {
            "LOGGING" : {
                "LOG_LEVEL" : "DEBUG", // or CRITICAL, ERROR, WARNING, INFO, DEBUG
                "LOG_FILE" : "bot.log"
            }
        }



# How to install and run the bot
### 1. Install Python Version 3 (I'm using 3.9.7 but ealier versions should work as well)

### 2. Navigate to the dca_bot directory
Linux:

        .../dca_binance_investment_bot $ cd dca_bot

Windows:

        ...\dca_binance_investment_bot> cd dca_bot

### 3. (Recommended) Install a virtual environment for the python modules 

Linux:

        .../dca_binance_investment_bot/dca_bot $ python -m venv env

Windows:

        ...\dca_binance_investment_bot\dca_bot> python -m venv env
        
(venv should be included with python 3.5+ for more info see: https://docs.python.org/3/library/venv.html)

### 3.1 Activate the virtual environment (Only necessary if step 3 was done)

Linux:

        .../dca_binance_investment_bot/dca_bot $ source env/bin/activate

Windows:

        dca_binance_investment_bot\dca_bot> .\env\Scripts\activate.bat

        or for Powershell:

        dca_binance_investment_bot\dca_bot> .\env\Scripts\activate.ps1

Afterwards you should see a (env) at the beginning of the line:

Linux

        (env) .../dca_binance_investment_bot/dca_bot $ 

Windows

        (env) ...\dca_binance_investment_bot\dca_bot>

To be really sure you're using the correct python installation, you can use:

Linux:

        which python

Windows:

        where.exe python
        (the '.exe' is neccessary for powershell and can be omitted when using normal cmd)

Make sure the path points to the correct python installation.
It should point to the python program inside the env directory:

Linux:
    
        .../dca_binance_investment_bot/dca_bot/env/bin/python

Windows:
    
        dca_binance_investment_bot\dca_bot\env\Scripts\python.exe

(windows might show multiple paths, the first one is relevant)

<br />
<br />
<br />
<br />

Sidenote: If you want to deactivate the virtual environment run:

Linux

        .../dca_binance_investment_bot/dca_bot $ deactivate

Windows

        ...\dca_binance_investment_bot\dca_bot> deactivate
<br />
<br />
<br />
<br />

### 4. Install the dependencies
To install the requirements use:

Linux:

        .../dca_binance_investment_bot/dca_bot $ python -m pip install -r requirements.txt

Windows
        
        ...\dca_binance_investment_bot\dca_bot> python -m pip install -r requirements.txt

### 5. Run the bot
Linux:

        .../dca_binance_investment_bot/dca_bot $ python main.py

Windows:

        ...\dca_binance_investment_bot\dca_bot> python main.py
