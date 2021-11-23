import datetime
import typing

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import dca_investment_bot.global_vars as global_vars
from dca_investment_bot.logger import LOG_DEBUG

COLLECTION_NOTIFICATION_IDS = "notification_ids"
COLLECTION_FULFILLED_ORDERS = "fulfilled_orders"

KEY_ORDER_TITLE = "title"
KEY_ORDER_BODY = "body"
KEY_ORDER_DATE = "date"


class FirebaseStorage:
    def __init__(self, project_id) -> None:
        # Use the application default credentials
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(
            cred,
            {
                "projectId": project_id,
            },
        )

        self.connected = False
        self.db: firestore.Client = None

    def connect(self):
        self.db = firestore.client()
        self.connected = True

    def __check_connection(self):
        if not self.connected:
            raise Exception("Not connected to firebase")

    def get_id(self, android_id: str) -> str:
        self.__check_connection()
        doc_ref = self.db.collection(COLLECTION_NOTIFICATION_IDS).document(android_id)
        return str(doc_ref.get().to_dict()["messaging_token"])

    def get_all_ids(self) -> typing.List:
        self.__check_connection()
        users = self.db.collection(COLLECTION_NOTIFICATION_IDS).stream()
        ids = []
        for user in users:
            ids.append(user.to_dict()["messaging_token"])
        return ids

    def set_fulfilled_orders(self, orders: typing.List) -> None:
        self.__check_connection()

        if not global_vars.sync_fulfilled_orders_to_firebase:
            LOG_DEBUG("Not syncing fulfilled orders to firebase: SYNC_FULFILLED_ORDERS_TO_FIREBASE is False")
            return

        LOG_DEBUG("Syncing fulfilled orders to firebase: SYNC_FULFILLED_ORDERS_TO_FIREBASE is True")
        fulfilled_orders = self.db.collection(COLLECTION_FULFILLED_ORDERS)
        for order in orders:
            fulfilled_orders.document(str(order.orderId)).set(
                {
                    KEY_ORDER_TITLE: order.symbol,
                    KEY_ORDER_BODY: order.to_info_string(),
                    KEY_ORDER_DATE: datetime.datetime.fromtimestamp(order.time / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
