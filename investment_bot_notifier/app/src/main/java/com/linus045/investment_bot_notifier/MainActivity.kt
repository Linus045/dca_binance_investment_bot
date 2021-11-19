package com.linus045.investment_bot_notifier

import android.content.Intent
import android.os.Build
import android.app.NotificationManager
import android.app.NotificationChannel
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.widget.Toast
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import com.google.firebase.messaging.FirebaseMessaging
import com.linus045.investment_bot_notifier.services.FirebaseCloudMessagingService

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            // Create channel to show notifications.
            val channelId = getString(R.string.default_notification_channel_id)
            val channelName = getString(R.string.default_notification_channel_name)
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager?.createNotificationChannel(NotificationChannel(channelId,
                channelName, NotificationManager.IMPORTANCE_LOW))
        }

        val sharedPrefs = getSharedPreferences(packageName, MODE_PRIVATE)
        val token = sharedPrefs.getString(FirebaseCloudMessagingService.MESSAGING_TOKEN_KEY, "")
        if(!token.isNullOrBlank()) {
            val android_id = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            val token_data = hashMapOf(
                "messaging_token" to token,
            )

            val db = Firebase.firestore
            db.collection("notification_ids").document(android_id)
                .set(token_data)
                .addOnSuccessListener { result ->
                    Log.d(TAG, "Updated token for user: " + android_id)
                    Toast.makeText(baseContext, "Updated token for user: " + android_id, Toast.LENGTH_LONG).show()
                }
                .addOnFailureListener { e ->
                    Log.e(TAG, "Error updating user token", e)
                    Toast.makeText(baseContext, "Error updating user token", Toast.LENGTH_LONG).show()
                }
        }else{
            Log.e(TAG, "No token found")
            Toast.makeText(baseContext, "No token found", Toast.LENGTH_LONG).show()
        }




//        FirebaseMessaging.getInstance().getToken().addOnCompleteListener({ task ->
//            if (!task.isSuccessful) {
//                Log.w(TAG, "Fetching FCM registration token failed", task.exception)
//                return@addOnCompleteListener
//            }
//
//            // Get new FCM registration token
//            val token = task.result
//
//            // Log and toast
//            val msg = getString(R.string.msg_token_fmt, token)
//            Log.d(TAG, msg)
//            Toast.makeText(baseContext, msg, Toast.LENGTH_SHORT).show()
//        })

    }
}