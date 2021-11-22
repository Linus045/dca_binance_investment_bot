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
        FIREBASE_SERVER_KEY=<Firebase Server Key here> (only neccessary when using firebase cloud messaging see below)
        GOOGLE_APPLICATION_CREDENTIALS=<path to json file> (only neccessary when using firebase cloud messaging see below)

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
                "LOG_LEVEL" : "DEBUG", // CRITICAL, ERROR, WARNING, INFO, DEBUG
                "LOG_FILE" : "bot.log"
            },
            "USE_TESTNET" : true,       // whether to use the testnet or the mainnet
            "CHECK_INTERVAL" : 1800,    // interval in seconds to check if a new investment is needed (default: 30min)
            "USE_FIREBASE" : false,     // whether to use firebase or not | will send relevant data to firestore and utilise cloud messaging to send info via the 'investment_bot_notifier' app to the user
            "FIREBASE_PROJECT_ID" : "investment-bot-notifier" // the project id of the firebase project (only needed if USE_FIREBASE : true)
            "SYNC_FULFILLED_ORDERS_TO_FIREBASE" : false, // whether to sync fulfilled orders to firebase or not (only needed if USE_FIREBASE : true)
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

Sidenote: If you want to deactivate the virtual environment run:

Linux

        .../dca_binance_investment_bot/dca_bot $ deactivate

Windows

        ...\dca_binance_investment_bot\dca_bot> deactivate
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


# How to connect the bot to Firebase (to receive messages via firebase cloud messaging and the investment_bot_notifier Android app)

### 1. Create a firebase project
Go to https://console.firebase.google.com/ and create a new project.

### 2. Copy the server key from the firebase project settings > cloud messaging > server key
See https://console.firebase.google.com/project/< YOUR-PROJECT-ID >/settings/cloudmessaging

This is needed to send messages to the user via firebase cloud messaging.
### 3. Copy the Firebase Admin SDK key from the firebase project settings > Service Accounts > Firebase Admin SDK
See https://console.firebase.google.com/project/< YOUR-PROJECT-ID >/settings/serviceaccounts/adminsdk

Click "Create new private key" and store the json file somewhere secure.
This is neccessary so the bot can store and load data from the firestore database (like device tokens and fulfilled orders).

### 4. Add the values to your enviorment variables (see .env.example)
Open the .env file and add the Cloud Messaging Server key and Firebase Admin SDK key.
Also don't forget to activate the Firebase options in the config.json file.

### 5. Create an Android app
Go to https://console.firebase.google.com/project/< YOUR-PROJECT-Id >/overview and create a new app.

Download the google-service.json file and place it in the root/investment_bot_notifier/app directory.

### 6. Open Android Studio and build the app
Open the app directory in Android Studio and build the app.

### 7. Run the app
Running the app on your phone/emulator is neccessary to receive messages via firebase cloud messaging.
Upon starting the app, you should see a toast notification (little popup at the bottom) on your phone/emulator which notifies you that your app token has been send to the firebase server (might need start the app twice in case the token hasn't been generated yet).

You should now see your token in the Firestore Database:
https://console.firebase.google.com/project/< YOUR-PROJECT-ID >/firestore/data

The document name is your unique Android ID and the messaging token is your unique Firebase token. (Usally does not change unless you reinstall the app/clear app data)
You can install this app on multiple devices and they all will receive the same notifications from the bot.
### 8. (Re-)start the bot 
You should now receive messages via firebase cloud messaging on your phone/emulator.