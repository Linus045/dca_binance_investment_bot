import time
import os

# A simple script to synchronize the time of the computer with the time of the server.
# try:
#     import ntplib
#     client = ntplib.NTPClient()
#     response = client.request('pool.ntp.org')

#     os.system('date ' + time.strftime('%m%d%H%M%Y.%S',time.localtime(response.tx_time)))
# except:
#     print('Could not sync with time server.')

# time sync on windows
os.system('net stop w32time')
os.system('net start w32time')
os.system('w32tm /resync')
os.system('w32tm /query /status')