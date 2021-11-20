# TODO: Change how Threads are stopped
# Used to stop all running threads
from firebase.firebase_messager import FirebaseMessager
from firebase.firebase_storage import FirebaseStorage

stop_threads = False


# TODO: Move this
firebaseStorage : FirebaseStorage = None
firebaseMessager : FirebaseMessager = None
notify_users = True