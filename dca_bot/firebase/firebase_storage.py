import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
from firebase_admin import firestore

COLLECTION_NOTIFICATION_IDS = u'notification_ids'

class FirebaseStorage:
    def __init__(self, project_id) -> None:
        # Use the application default credentials
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred, {
            'projectId': project_id,
        })

        self.connected = False
        self.db = None

    def connect(self):
        self.db = firestore.client()
        self.connected = True

    def __check_connection(self):
        if not self.connected:
            raise Exception('Not connected to firebase')
    
    def get_id(self, android_id : str) -> str:
        self.__check_connection()
        doc_ref = self.db.collection(COLLECTION_NOTIFICATION_IDS).document(android_id)
        return doc_ref.get().to_dict()

    def get_all_ids(self, bot_notification_id) -> list:
        self.__check_connection()
        users = self.db.collection(COLLECTION_NOTIFICATION_IDS).stream()
        ids = []
        for user in users:
            ids.append(user.to_dict()['messaging_token'])
        return ids
