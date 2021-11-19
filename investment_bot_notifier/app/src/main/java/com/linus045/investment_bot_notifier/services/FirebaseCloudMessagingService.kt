package com.linus045.investment_bot_notifier.services

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class FirebaseCloudMessagingService : FirebaseMessagingService {


    companion object {
        private const val TAG = "MyFirebaseMessagingService"
        const val MESSAGING_TOKEN_KEY = "Firebase_Messaging_Token"
    }

    constructor() : super()

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.e(TAG, "New Token: " + token)

        val sharedPrefs = getSharedPreferences(packageName, MODE_PRIVATE)
        val successful = sharedPrefs.edit().putString(MESSAGING_TOKEN_KEY, token).commit()
        if(!successful)
            Log.e(TAG, "Storing of token failed!")
    }


    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
    }

}