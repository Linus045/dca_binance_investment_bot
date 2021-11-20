package com.linus045.investment_bot_notifier

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.linus045.investment_bot_notifier.services.BotNotification

class NotificationViewHolder(view : View) : RecyclerView.ViewHolder(view) {
    private var title = "Some Title"
    private var body = "Some body"
    private var date = "0000-00-00 00:00"

    fun setData(data: BotNotification) {
        title = data.title
        body = data.body
        date = data.date
        textviewTitle.text = title
        textviewBody.text = body
        textViewDate.text = date
    }

    private val textviewTitle : TextView = view.findViewById(R.id.textViewTitle)
    private val textviewBody : TextView = view.findViewById(R.id.textViewBody)
    private val textViewDate : TextView = view.findViewById(R.id.textViewDate)
}

class NotificationListviewAdapter : RecyclerView.Adapter<NotificationViewHolder>() {
    private var fulfilledOrdersCount = 0
    private var fulfilledOrders = ArrayList<BotNotification>()

    init {
        fulfilledOrdersCount = 0
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): NotificationViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.order_card, parent, false)
        return NotificationViewHolder(view)
    }

    override fun onBindViewHolder(holder: NotificationViewHolder, position: Int) {
        if(position < fulfilledOrders.count())
            holder.setData(fulfilledOrders[position])
    }

    override fun getItemCount(): Int {
        return fulfilledOrdersCount
    }

    fun addNotification(notification: BotNotification) {
        fulfilledOrders.add(0, notification)
        this.notifyItemInserted(0)
        fulfilledOrdersCount++
    }

    fun clear() {
        this.notifyItemRangeRemoved(0, fulfilledOrdersCount)
        fulfilledOrders.clear()
        fulfilledOrdersCount = 0
    }
}