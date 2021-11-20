import os
from time import sleep

from dotenv import load_dotenv
from pyfcm import FCMNotification

from logger import LOG_DEBUG

class FirebaseMessager:

    def __init__(self) -> None:
        # load environment variables
        dotEnvPath = os.path.join('configs', '.env')
        if os.path.exists(dotEnvPath):
            load_dotenv(dotEnvPath)
        self.TAG = 'FirebaseMessager'
        self.key = os.environ.get('FIREBASE_SERVER_KEY')
        self.push_service = FCMNotification(api_key=self.key)
        self.ids = []

    def set_ids(self, ids: list) -> None:
        self.ids = ids

    def push_notification(self, title: str, body: str) -> None:
        if len(self.ids) == 0:
            return

        message_title = title
        message_body = body

        try:
            result = self.push_service.notify_multiple_devices(registration_ids=self.ids, message_title=message_title, message_body=message_body)
            # TODO: Handle error cases here
            LOG_DEBUG(self.TAG, str(result))
        except:
            pass
