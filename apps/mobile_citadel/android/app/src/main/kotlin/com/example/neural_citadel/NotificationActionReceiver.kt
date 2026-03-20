package com.example.neural_citadel

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class NotificationActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        Log.d("NeuralAuth", "Notification Action: $action")
        
        when (action) {
            "ANSWER_CALL" -> {
                CallService.activeCall?.answer(0) // 0 = Audio Only
                // Notification will update automatically via onStateChanged -> showNotification
            }
            "END_CALL" -> {
                val call = CallService.activeCall
                if (call != null) {
                    if (call.state == android.telecom.Call.STATE_RINGING) {
                        call.reject(false, null)
                    } else {
                        call.disconnect()
                    }
                }
            }
            "TOGGLE_SPEAKER" -> {
                CallService.cycleSpeaker()
            }
            "TOGGLE_MUTE" -> {
                CallService.cycleMute()
            }
        }
        
        // Note: ACTION_CLOSE_SYSTEM_DIALOGS is restricted on Android 12+ for non-system apps
    }
}
