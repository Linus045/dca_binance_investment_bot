# dca_binance_investment_bot
A bot that automatically invest using the DCA (Dollar Cost Averaging) strategy

dca_bot contains the relevant code for the bot.
timesync contains the code for the time synchronization (Currently not integrated).


# Steps to run the bot
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
