package com.linus045.investment_bot_notifier

import android.os.Build
import android.app.NotificationManager
import android.app.NotificationChannel
import android.content.Context
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.provider.Settings
import android.util.AttributeSet
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout.OnRefreshListener
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import com.linus045.investment_bot_notifier.services.BotNotification
import com.linus045.investment_bot_notifier.services.FirebaseCloudMessagingService

class MainActivity : AppCompatActivity(), OnRefreshListener {

    companion object {
        private const val TAG = "MainActivity"

        private val KEY_ORDER_TITLE = "title"
        private val KEY_ORDER_BODY = "body"
        private val KEY_ORDER_DATE = "date"
        private val KEY_FULFILLED_ORDERS = "fulfilled_orders"
    }

    override fun onCreateView(
        parent: View?,
        name: String,
        context: Context,
        attrs: AttributeSet
    ): View? {
        return super.onCreateView(parent, name, context, attrs)
    }

    fun pullFulfilledOrders() {
        Log.e(TAG, "pullFulfilledOrders")
        if(notificationListviewAdapter == null)
            return

        Log.e(TAG, "pullFulfilledOrders")

        val db = Firebase.firestore
        val fulfilledOrdersCollection = db.collection(KEY_FULFILLED_ORDERS)
        fulfilledOrdersCollection.get().addOnSuccessListener {
            if(notificationListviewAdapter != null) {
                Log.e(TAG, "Rertieved Documents: " + it.documents.size)
                notificationListviewAdapter!!.clear()
                it.documents.forEach { doc ->
                    val title = doc[KEY_ORDER_TITLE].toString()
                    val body = doc[KEY_ORDER_BODY].toString()
                    val date = doc[KEY_ORDER_DATE].toString()
                    notificationListviewAdapter!!.addNotification(BotNotification(title, body, date))
                }
            }
        }.addOnFailureListener {
            Log.e(TAG, "No messages found")
            Toast.makeText(baseContext, "no Messages found", Toast.LENGTH_LONG).show()
        }
    }

    private var notificationListviewAdapter : NotificationListviewAdapter? = null;
    private var swipeLayout: SwipeRefreshLayout? = null

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

        val db = Firebase.firestore

        if(!token.isNullOrBlank()) {
            val android_id = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            val token_data = hashMapOf(
                "messaging_token" to token,
            )

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

        notificationListviewAdapter = NotificationListviewAdapter()
        swipeLayout = findViewById(R.id.swipeLayout)
        swipeLayout?.setOnRefreshListener(this)
        val fulfilledOrdersListview = findViewById<RecyclerView>(R.id.fulfilled_orders_listview)
        fulfilledOrdersListview.adapter = notificationListviewAdapter


        pullFulfilledOrders()

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

    override fun onRefresh() {
        Log.e(TAG, "REFRESHING")
        swipeLayout?.isRefreshing = true
        pullFulfilledOrders()
        swipeLayout?.isRefreshing = false
    }
}