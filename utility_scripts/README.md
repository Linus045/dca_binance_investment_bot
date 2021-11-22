This is a systemd service to automatically run a script on boot and stop it gracefully on shutdown.
The service will automatically restart on failure.
To Install the systemd service:

# 1 . Copy the example file:
```
copy:
cp dca_trading_bot.service.example dca_trading_bot.service
```

# 2. Set the corrct user/group:
Replace the User and Group with the correct user/group name.
This is the user/group that will run the script.

# 3. Set the correct path to the working directory:
Set the path for 'WorkingDirectory' to the directory where the `main.py` script is located.

e.g. with the `main.py` script at `/home/pi/dca_trading_bot/main.py`
```
WorkingDirectory=/home/pi/dca_trading_bot
``` 

# 4. Set the correct path for ExecStart:
Change the python path to the correct python bin directory. 
If you are using a virtual environment, you need to set the path to the virtual environment.

e.g. 
```
ExecStart=/home/pi/dca_bot/env/bin/python main.py
```

# 4.1 Example of the systemd service file:
```
[Unit]
Description=DCA Trading Bot
Documentation=https://github.com/Linus045/dca_binance_investment_bot
After=network.target
StartLimitIntervalSec=180
StartLimitBurst=3

[Service]
Type=exec
User=pi
Group=pi
WorkingDirectory=/home/pi/dca_bot
ExecStart=/home/pi/dca_bot/env/bin/python main.py
KillSignal=SIGTERM
RestartSec=10
TimeoutStopSec=10
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

# 5 Copy or move script to systemd service folder:
```
copy:
cp dca_trading_bot.service /etc/systemd/system/dca_trading_bot.service

move:
sudo mv dca_trading_bot.service /etc/systemd/system/dca_trading_bot.service
```

# 6. Enable the service:
```
sudo systemctl enable dca_trading_bot.service.service
```

Service fails if the script fails 3 times in a row (in 180 seconds).




# Troubleshooting/Debugging:
To see the status of the service:
```
sudo systemctl status dca_trading_bot.service
```

or to see the logs:
```
sudo journalctl -u dca_trading_bot.service
```

To reset the service on failure (if the service fails to start 3 times in a row):
```
sudo systemctl reset-failed dca_trading_bot.service
```
