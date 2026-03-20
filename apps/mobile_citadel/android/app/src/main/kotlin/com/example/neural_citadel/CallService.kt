package com.example.neural_citadel

import android.content.Intent
import android.telecom.Call
import android.telecom.CallAudioState
import android.telecom.InCallService
import android.telecom.VideoProfile // RE-ADDED For Video Calls
import android.provider.ContactsContract // ADDED for createContact
import android.util.Log
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Person
import android.graphics.drawable.Icon
import android.os.Build
import androidx.core.app.NotificationCompat

class CallService : InCallService() {
    
    private val CHANNEL_ID = "neural_call_channel"          // Incoming: IMPORTANCE_HIGH (heads-up + lock screen)
    private val CHANNEL_ID_ONGOING = "neural_call_ongoing"   // Active: IMPORTANCE_DEFAULT (no popup, green chip)
    private val NOTIFICATION_ID = 101

    private var prefsListener: android.content.SharedPreferences.OnSharedPreferenceChangeListener? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        setupOverlayActionBridge()
    }

    private fun setupOverlayActionBridge() {
        val prefs = getSharedPreferences("FlutterSharedPreferences", android.content.Context.MODE_PRIVATE)
        prefsListener = android.content.SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
            if (key == "flutter.actionEvent_answer_call") {
                activeCall?.answer(0)
            } else if (key == "flutter.actionEvent_end_call") {
                val c = activeCall
                if (c != null) {
                    if (c.state == Call.STATE_RINGING) c.reject(false, null) else c.disconnect()
                }
            } else if (key == "flutter.actionEvent_speaker_on") {
                setSpeaker(true)
            } else if (key == "flutter.actionEvent_speaker_off") {
                setSpeaker(false)
            }
        }
        prefs.registerOnSharedPreferenceChangeListener(prefsListener)
    }

    override fun onDestroy() {
        super.onDestroy()
        prefsListener?.let {
            getSharedPreferences("FlutterSharedPreferences", android.content.Context.MODE_PRIVATE)
                .unregisterOnSharedPreferenceChangeListener(it)
        }
        // Safety net: kill any lingering notification when service is destroyed
        killNotification()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java)
            
            // Channel for INCOMING calls: HIGH importance = heads-up + full screen intent
            val incoming = NotificationChannel(
                CHANNEL_ID,
                "Incoming Calls",
                NotificationManager.IMPORTANCE_HIGH
            )
            manager.createNotificationChannel(incoming)
            
            // Channel for ONGOING calls: DEFAULT importance = no popup, but visible in status bar
            val ongoing = NotificationChannel(
                CHANNEL_ID_ONGOING,
                "Ongoing Calls",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            ongoing.setSound(null, null) // No sound for ongoing call notification
            manager.createNotificationChannel(ongoing)
        }
    }

    /**
     * Nuclear notification kill — uses every available method to remove the notification.
     * Safe to call multiple times (idempotent).
     */
    /**
     * Broadcasts real-time state to ALL listening Flutter Isolates (Main UI and Dynamic Island).
     */
    private fun broadcastCallState() {
        try {
             MainActivity.eventSink?.success(mapOf("event" to "state_sync", "data" to getAllCallsState()))
        } catch (_: Exception) {}
        try {
             MainActivity.instance?.sendEvent("state_sync", getAllCallsState())
        } catch (_: Exception) {}
    }

    private fun killNotification() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                stopForeground(STOP_FOREGROUND_REMOVE)
            } else {
                @Suppress("DEPRECATION")
                stopForeground(true)
            }
        } catch (e: Exception) {
            Log.e("CallService", "stopForeground failed: ${e.message}")
        }
        try {
            val nm = getSystemService(NotificationManager::class.java)
            nm.cancel(NOTIFICATION_ID)
        } catch (e: Exception) {
            Log.e("CallService", "NotificationManager.cancel failed: ${e.message}")
        }
    }

    fun showNotification(call: Call) {
        try {
            // GUARD: Skip for dead calls to prevent accessing invalid properties
            if (call.state == Call.STATE_DISCONNECTED || call.state == Call.STATE_DISCONNECTING) {
                Log.d("CallService", "showNotification skipped: call is disconnected")
                return
            }
            
            val intent = Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
            }
            val pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)

            var name = try { call.details.callerDisplayName } catch (_: Exception) { null }
            if (name.isNullOrEmpty()) {
                val handle = call.details.handle
                if (handle != null) {
                    try {
                        val uri = android.net.Uri.withAppendedPath(android.provider.ContactsContract.PhoneLookup.CONTENT_FILTER_URI, android.net.Uri.encode(handle.schemeSpecificPart))
                        val cursor = contentResolver.query(uri, arrayOf(android.provider.ContactsContract.PhoneLookup.DISPLAY_NAME), null, null, null)
                        cursor?.use {
                            if (it.moveToFirst()) {
                                name = it.getString(0)
                            }
                        }
                    } catch (e: Exception) {}
                }
                if (name.isNullOrEmpty()) {
                     name = "Unknown Call"
                }
            }
            val isRinging = call.state == Call.STATE_RINGING
            
            // Actions
            val ansIntent = Intent(this, NotificationActionReceiver::class.java).setAction("ANSWER_CALL")
            val ansPending = PendingIntent.getBroadcast(this, 1, ansIntent, PendingIntent.FLAG_IMMUTABLE)
            
            val endIntent = Intent(this, NotificationActionReceiver::class.java).setAction("END_CALL")
            val endPending = PendingIntent.getBroadcast(this, 2, endIntent, PendingIntent.FLAG_IMMUTABLE)
            
            val spkIntent = Intent(this, NotificationActionReceiver::class.java).setAction("TOGGLE_SPEAKER")
            val spkPending = PendingIntent.getBroadcast(this, 3, spkIntent, PendingIntent.FLAG_IMMUTABLE)

            val notification: android.app.Notification
            
            // Premium Dark Theme
            val premiumColor = android.graphics.Color.parseColor("#121212")

            if (Build.VERSION.SDK_INT >= 31) {
                val person = Person.Builder()
                    .setName(name)
                    .setIcon(Icon.createWithResource(this, R.mipmap.launcher_icon))
                    .setImportant(true)
                    .build()
                
                val style = if (isRinging) {
                     // Note: CallStyle actions use the intents passed here for the main large buttons
                     android.app.Notification.CallStyle.forIncomingCall(person, endPending, ansPending)
                } else {
                     android.app.Notification.CallStyle.forOngoingCall(person, endPending)
                }
                
                val channelId = CHANNEL_ID_ONGOING 
                
                val builder = android.app.Notification.Builder(this, channelId)
                    .setSmallIcon(R.drawable.ic_notification_answer) 
                    .setContentIntent(pendingIntent)
                    .setStyle(style)
                    .setCategory(android.app.Notification.CATEGORY_CALL)
                    .setColor(premiumColor)
                    .setColorized(true)
                    .setOngoing(true)
                
                // Full screen intent ONLY for incoming calls (lock screen) & when app is NOT visible
                if (isRinging && !MainActivity.isAppVisible) {
                    builder.setFullScreenIntent(pendingIntent, true)
                }
                
                if (!isRinging) {
                     val isSpeaker = callAudioState?.route == CallAudioState.ROUTE_SPEAKER
                     val spkAction = android.app.Notification.Action.Builder(
                         Icon.createWithResource(this, R.drawable.ic_notification_speaker), 
                         if (isSpeaker) "Speaker OFF" else "Speaker ON", 
                         spkPending
                     ).build()
                     builder.addAction(spkAction)

                     val isMuted = callAudioState?.isMuted ?: false
                     val muteIntent = Intent(this, NotificationActionReceiver::class.java).setAction("TOGGLE_MUTE")
                     val mutePending = PendingIntent.getBroadcast(this, 4, muteIntent, PendingIntent.FLAG_IMMUTABLE)
                     
                     val muteIconRes = if (isMuted) R.drawable.ic_notification_unmute else R.drawable.ic_notification_mute
                     val muteLabel = if (isMuted) "Unmute" else "Mute"
                     
                     // For Android 12+ Builder
                     val muteAction = android.app.Notification.Action.Builder(
                         Icon.createWithResource(this, muteIconRes), 
                         muteLabel, 
                         mutePending
                     ).build()
                     builder.addAction(muteAction)
                }
                notification = builder.build()
            } else {
                val channelId = CHANNEL_ID_ONGOING
                
                val builder = NotificationCompat.Builder(this, channelId)
                    .setContentTitle(if (isRinging) "Incoming Call" else "Active Call")
                    .setContentText(name)
                    .setSmallIcon(R.drawable.ic_notification_answer)
                    .setContentIntent(pendingIntent)
                    .setOngoing(true)
                    .setCategory(NotificationCompat.CATEGORY_CALL)
                    .setColor(premiumColor)
                    .setColorized(true)
                
                // Full screen intent ONLY for incoming calls & when app is NOT visible
                if (isRinging && !MainActivity.isAppVisible) {
                    builder.setFullScreenIntent(pendingIntent, true)
                }

                if (isRinging) {
                     builder.addAction(R.drawable.ic_notification_answer, "Answer", ansPending)
                     builder.addAction(R.drawable.ic_notification_end_call, "Decline", endPending)
                } else {
                     val isSpeaker = callAudioState?.route == CallAudioState.ROUTE_SPEAKER
                     builder.addAction(R.drawable.ic_notification_speaker, if (isSpeaker) "Speaker OFF" else "Speaker ON", spkPending)
                     
                     val isMuted = callAudioState?.isMuted ?: false
                     val muteIntent = Intent(this, NotificationActionReceiver::class.java).setAction("TOGGLE_MUTE")
                     val mutePending = PendingIntent.getBroadcast(this, 4, muteIntent, PendingIntent.FLAG_IMMUTABLE)
                     
                     val muteIconRes = if (isMuted) R.drawable.ic_notification_unmute else R.drawable.ic_notification_mute
                     val muteLabel = if (isMuted) "Unmute" else "Mute"

                     builder.addAction(muteIconRes, muteLabel, mutePending)
                     
                     builder.addAction(R.drawable.ic_notification_end_call, "End Call", endPending)
                }
                notification = builder.build()
            }

            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                     startForeground(NOTIFICATION_ID, notification, 
                         android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_PHONE_CALL)
                } else {
                     startForeground(NOTIFICATION_ID, notification)
                }
            } catch (e: Exception) {
                Log.e("CallService", "showNotification startForeground failed: ${e.message}")
                try {
                    val nm = getSystemService(android.app.NotificationManager::class.java)
                    nm.notify(NOTIFICATION_ID, notification)
                } catch (_: Exception) {}
            }
        } catch (e: Exception) {
            Log.e("CallService", "FATAL showNotification Crash Caught: ${e.message}")
            e.printStackTrace()
        }
    }

    companion object {
        private val calls = ArrayList<Call>() // Explicit ArrayList for guaranteed mutability
        
        var activeCall: Call? = null
        var lastKnownCall: Call? = null
        var serviceInstance: CallService? = null

        fun toggleHold(on: Boolean) {
            activeCall?.let {
                if (on) it.hold() else it.unhold()
            }
        }

        fun setMute(muted: Boolean) {
            serviceInstance?.setMuted(muted)
        }

        fun cycleMute() {
            val current = serviceInstance?.callAudioState?.isMuted ?: false
            setMute(!current)
        }

        fun setSpeaker(on: Boolean) {
            val ctx = serviceInstance

            
            if (on) {
                serviceInstance?.setAudioRoute(CallAudioState.ROUTE_SPEAKER)
            } else {
                serviceInstance?.setAudioRoute(CallAudioState.ROUTE_EARPIECE)
            }
        }

        fun createContact(number: String?) {
            val ctx = serviceInstance
            if (ctx != null && number != null) {
                val intent = Intent(Intent.ACTION_INSERT_OR_EDIT).apply {
                    type = ContactsContract.Contacts.CONTENT_ITEM_TYPE
                    putExtra(ContactsContract.Intents.Insert.PHONE, number)
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                ctx.startActivity(intent)
            } else {
                Log.e("CallService", "createContact: Service instance or number is null")
            }
        }

        fun cycleSpeaker() {
            val current = serviceInstance?.callAudioState?.route == CallAudioState.ROUTE_SPEAKER
            setSpeaker(!current)
            activeCall?.let { serviceInstance?.showNotification(it) }
        }

        fun getAudioRoutes(): Map<String, Any> {
            val state = serviceInstance?.callAudioState ?: return mapOf()
            val available = ArrayList<Int>()
            
            if ((state.supportedRouteMask and CallAudioState.ROUTE_EARPIECE) != 0) available.add(CallAudioState.ROUTE_EARPIECE)
            if ((state.supportedRouteMask and CallAudioState.ROUTE_SPEAKER) != 0) available.add(CallAudioState.ROUTE_SPEAKER)
            if ((state.supportedRouteMask and CallAudioState.ROUTE_BLUETOOTH) != 0) available.add(CallAudioState.ROUTE_BLUETOOTH)
            if ((state.supportedRouteMask and CallAudioState.ROUTE_WIRED_HEADSET) != 0) available.add(CallAudioState.ROUTE_WIRED_HEADSET)

            return mapOf(
                "active" to state.route,
                "available" to available
            )
        }

        fun setAudioRoute(route: Int) {
            serviceInstance?.setAudioRoute(route)
        }

        fun requestBluetoothAudio(address: String) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                try {
                    val device = serviceInstance?.callAudioState?.supportedBluetoothDevices?.find { it.address == address }
                    if (device != null) {
                        serviceInstance?.requestBluetoothAudio(device)
                    }
                } catch (e: SecurityException) {
                    Log.e("CallService", "Missing Bluetooth Permissions")
                }
            }
        }

        fun mergeCalls() {
            // Smart Merge: Active + Background
            val fg = calls.firstOrNull { it.state == Call.STATE_ACTIVE }
            val bg = calls.firstOrNull { it.state == Call.STATE_HOLDING }
            
            if (fg != null && bg != null) {
                fg.mergeConference()
            } else {
                activeCall?.mergeConference()
            }
        }

        // Placeholder for swap if needed
        private var recorder: android.media.MediaRecorder? = null
        private var recordingUri: android.net.Uri? = null

        fun toggleRecording(on: Boolean) {
             if (on) {
                 startRecording()
             } else {
                 stopRecording()
             }
        }

        private fun startRecording() {
            val ctx = serviceInstance ?: return
            try {
                val values = android.content.ContentValues().apply {
                    put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, "Call_${System.currentTimeMillis()}.m4a")
                    put(android.provider.MediaStore.MediaColumns.MIME_TYPE, "audio/mp4")
                    put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH, android.os.Environment.DIRECTORY_MUSIC + "/CallRecordings")
                }
                
                val uri = ctx.contentResolver.insert(android.provider.MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, values)
                    ?: throw java.io.IOException("MediaStore Create Failed")
                
                recordingUri = uri
                
                val pfd = ctx.contentResolver.openFileDescriptor(uri, "w") 
                    ?: throw java.io.IOException("Failed to open FD")
                
                recorder = android.media.MediaRecorder().apply {
                    // Reverted to MIC to prevent blocking Voice Agent
                    setAudioSource(android.media.MediaRecorder.AudioSource.MIC)
                    setOutputFormat(android.media.MediaRecorder.OutputFormat.MPEG_4)
                    setAudioEncoder(android.media.MediaRecorder.AudioEncoder.AAC)
                    setOutputFile(pfd.fileDescriptor)
                    prepare()
                    start()
                } 
                
                android.widget.Toast.makeText(ctx, "Recording Started", android.widget.Toast.LENGTH_SHORT).show()
                
            } catch(e: Exception) {
                Log.e("CallService", "Rec fail: ${e.message}")
                android.widget.Toast.makeText(ctx, "Rec Error: ${e.message}", android.widget.Toast.LENGTH_SHORT).show()
            }
        }

        private fun stopRecording() {
            try {
                recorder?.apply {
                    stop()
                    release()
                }
                serviceInstance?.let {
                   android.widget.Toast.makeText(it, "Saved to Music/CallRecordings", android.widget.Toast.LENGTH_LONG).show()
                }
            } catch(e: Exception) {
                 Log.e("CallService", "Stop fail: ${e.message}")
            } finally {
                recorder = null // CRITICAL: Always release memory reference
                recordingUri = null
            }
        }

        // Helper to auto-save on disconnect
        fun autoSave() {
            if (recorder != null) {
                stopRecording()
            }
        }

        fun swapCalls() {
            val fg = calls.firstOrNull { it.state == Call.STATE_ACTIVE }
            val bg = calls.firstOrNull { it.state == Call.STATE_HOLDING }

            if (fg != null && bg != null) {
                fg.hold()
                bg.unhold()
            }
        }
        
        // HYBRID CONTRACT IMPLEMENTATION
        fun getAllCallsState(): Map<String, Any?> {
             val map = HashMap<String, Any?>()
             
             // 0. GLOBAL AUDIO STATE (Must be at top to survive hardware fallback early returns)
             val isMuted = serviceInstance?.callAudioState?.isMuted ?: false
             map["isMuted"] = isMuted
             val isSpeaker = serviceInstance?.callAudioState?.route == CallAudioState.ROUTE_SPEAKER
             map["isSpeaker"] = isSpeaker
             val audioState = serviceInstance?.callAudioState
             if (audioState != null) {
                 map["audioRoute"] = audioState.route
                 map["supportedAudioRoutes"] = audioState.supportedRouteMask
                 
                 if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
                     try {
                         val devices = audioState.supportedBluetoothDevices.map { 
                             mapOf("name" to (it.name), "address" to it.address) 
                         }
                         map["supportedBluetoothDevices"] = devices
                         map["activeBluetoothDevice"] = audioState.activeBluetoothDevice?.let { 
                             mapOf("name" to (it.name), "address" to it.address) 
                         }
                     } catch (e: SecurityException) {
                         // Permission missing
                     } catch (e: Exception) {
                         Log.e("CallService", "Error reading BT devices: \${e.message}")
                     }
                 }
             }

             // 1. FILTER ZOMBIES — exclude dead calls to prevent stale UI/notification
             val validCalls = calls.filter { 
                 it.state != Call.STATE_DISCONNECTED && 
                 it.state != Call.STATE_DISCONNECTING 
             }
             
             if (validCalls.isEmpty()) {
                 try {
                     val tm = serviceInstance?.getSystemService(android.telecom.TelecomManager::class.java)
                     if (tm != null && tm.isInCall) {
                         val telMgr = serviceInstance?.getSystemService(android.telephony.TelephonyManager::class.java)
                         val isRingingFallback = telMgr?.callState == android.telephony.TelephonyManager.CALL_STATE_RINGING
                         
                         map["state"] = if (isRingingFallback) android.telecom.Call.STATE_RINGING else android.telecom.Call.STATE_ACTIVE
                         map["isIncoming"] = isRingingFallback
                         
                         // Use cached details from the last active call to preserve identity
                         var cachedNumber = ""
                         var cachedName = ""
                         
                         val c = activeCall ?: calls.lastOrNull() ?: lastKnownCall
                         if (c != null) {
                              cachedName = c.details.callerDisplayName ?: ""
                              if (c.details.handle != null) {
                                  val rawVal = android.net.Uri.decode(c.details.handle.schemeSpecificPart)
                                  if (!rawVal.isNullOrEmpty()) cachedNumber = rawVal
                              } else if (c.details.gatewayInfo?.originalAddress != null) {
                                  val rawVal = android.net.Uri.decode(c.details.gatewayInfo?.originalAddress?.schemeSpecificPart)
                                  if (!rawVal.isNullOrEmpty()) cachedNumber = rawVal
                              }
                         }
                         
                         if (cachedNumber.isEmpty()) cachedNumber = "Unknown Number"
                         if (cachedName.isEmpty()) cachedName = "Unknown"
                         
                         map["number"] = cachedNumber
                         map["name"] = cachedName
                         return map
                     }
                 } catch (e: Exception) {}
                 return mapOf()
             }

             // 1. IDENTIFY PRIMARY CALL (Ringing Preferred over Active to guarantee UI popup)
             val primary = validCalls.firstOrNull { it.state == Call.STATE_RINGING } 
                           ?: activeCall 
                           ?: validCalls.lastOrNull()
             
             if (primary != null) {
                 // --- LEGACY MAPPING (Directly on Root) ---
                 map["state"] = primary.state
                 map["isIncoming"] = (primary.state == Call.STATE_RINGING)
                 
                 // Extract Number (Logic from redundant mapCall)
                 var number = ""
                 if (primary.details.handle != null) {
                      number = android.net.Uri.decode(primary.details.handle.schemeSpecificPart)
                 }
                 if (number.isNullOrEmpty()) {
                      if (primary.details.gatewayInfo?.originalAddress != null) {
                           number = android.net.Uri.decode(primary.details.gatewayInfo?.originalAddress?.schemeSpecificPart)
                      }
                 }
                 map["number"] = number
                 map["name"] = primary.details.callerDisplayName ?: ""
                 // -----------------------------------------
                 
                 // 2. NEW NESTED MAPPING (For Feature-Rich UI)
                 val activeData = mapCall(primary)
                 if (activeData != null) map["active"] = activeData
             }
             
             // 3. BACKGROUND CALL
             val bg = validCalls.firstOrNull { it.state == Call.STATE_HOLDING }
             if (bg != null) {
                 val bgData = mapCall(bg)
                 if (bgData != null) map["background"] = bgData
             }
             
             // 4. CONFERENCE DATA (For List UI)
             // Check if ANY call is a conference or has children
             val confCall = validCalls.firstOrNull { !it.children.isNullOrEmpty() } 
                         ?: validCalls.firstOrNull { it.details.hasProperty(Call.Details.PROPERTY_CONFERENCE) }
             
             if (confCall != null) {
                 map["conference"] = true
                 
                 // EXTRACT PARTICIPANTS
                 val participants = ArrayList<Map<String, Any?>>()
                 if (!confCall.children.isNullOrEmpty()) {
                     for (child in confCall.children) {
                         val childData = mapCall(child)
                         if (childData != null) participants.add(childData)
                     }
                 }
                 map["participants"] = participants
             }

             return map
        }
             
        private fun mapCall(c: Call): Map<String, Any?>? {
             val m = HashMap<String, Any?>()
             m["state"] = c.state
             m["isIncoming"] = (c.state == Call.STATE_RINGING)
             
             var number = ""
             var debugInfo = "Raw: "
             
             if (c.details.handle != null) {
                 val rawVal = c.details.handle.schemeSpecificPart
                 debugInfo += "H($rawVal) "
                 number = android.net.Uri.decode(rawVal)
             } else {
                 debugInfo += "H(NULL) "
             }
             
             if (number.isNullOrEmpty()) {
                 if (c.details.gatewayInfo?.originalAddress != null) {
                     val gwVal = c.details.gatewayInfo?.originalAddress?.schemeSpecificPart
                     debugInfo += "G($gwVal)"
                     number = android.net.Uri.decode(gwVal)
                 } else {
                     debugInfo += "G(NULL)"
                 }
             }
             
             m["number"] = number
             m["name"] = c.details.callerDisplayName ?: ""
             m["debug"] = debugInfo // Persist Debug Info for UI
             
             // Zombie Check (Prevents Ghost Calls in Nested Logic)
             if ((number.isNullOrEmpty() || number == "null" || number == "Unknown") && (m["name"] as String).isEmpty()) {
                 return null
             }
             return m
        }
        
        private var dtmfGenerator: android.media.ToneGenerator? = null

        fun playDtmf(key: Char) {
            val c = activeCall
            if (c != null) {
                // Active Call: Use Telecom API (Network + System Feedback)
                try {
                    c.playDtmfTone(key)
                    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                        c.stopDtmfTone()
                    }, 200)
                } catch (e: Exception) {
                    Log.e("CallService", "DTMF Failed: ${e.message}")
                }
            } else {
                // No Call: Local Feedback (Dialer Mode)
                try {
                    if (dtmfGenerator == null) {
                        try {
                            // Use STREAM_MUSIC to ensure audibility even if system system/dtmf sounds are disabled
                            dtmfGenerator = android.media.ToneGenerator(android.media.AudioManager.STREAM_MUSIC, 100)
                        } catch (e: Exception) {
                            Log.e("CallService", "ToneGen Init Failed: ${e.message}")
                        }
                    }
                    
                    val toneType = when (key) {
                        '0' -> android.media.ToneGenerator.TONE_DTMF_0
                        '1' -> android.media.ToneGenerator.TONE_DTMF_1
                        '2' -> android.media.ToneGenerator.TONE_DTMF_2
                        '3' -> android.media.ToneGenerator.TONE_DTMF_3
                        '4' -> android.media.ToneGenerator.TONE_DTMF_4
                        '5' -> android.media.ToneGenerator.TONE_DTMF_5
                        '6' -> android.media.ToneGenerator.TONE_DTMF_6
                        '7' -> android.media.ToneGenerator.TONE_DTMF_7
                        '8' -> android.media.ToneGenerator.TONE_DTMF_8
                        '9' -> android.media.ToneGenerator.TONE_DTMF_9
                        '*' -> android.media.ToneGenerator.TONE_DTMF_S
                        '#' -> android.media.ToneGenerator.TONE_DTMF_P
                        else -> -1
                    }
                    
                    if (toneType != -1) {
                        dtmfGenerator?.startTone(toneType, 150) // Play for 150ms
                    }
                } catch (e: Exception) {
                     Log.e("CallService", "Local Tone Failed: ${e.message}")
                }
            }
        }
        
        fun acceptVideoUpgrade() { // RE-ADDED
            try {
                val videoProfile = VideoProfile(VideoProfile.STATE_BIDIRECTIONAL)
                activeCall?.videoCall?.sendSessionModifyResponse(videoProfile)
            } catch (e: Exception) {
                Log.e("CallService", "Failed to accept video: ${e.message}")
            }
        }
    }

    override fun onCallAudioStateChanged(audioState: CallAudioState?) {
        try {
            super.onCallAudioStateChanged(audioState)
            val target = activeCall ?: calls.lastOrNull()
            // Guard: don't re-show notification for dead/disconnected calls
            if (target != null && target.state != Call.STATE_DISCONNECTED && target.state != Call.STATE_DISCONNECTING) {
                showNotification(target)
            }
        } catch (e: Exception) {
            Log.e("CallService", "onCallAudioStateChanged error: ${e.message}")
        }
    }

    override fun onCallAdded(call: Call) {
        serviceInstance = this
        try {
            super.onCallAdded(call)
        } catch (e: Exception) {
            Log.e("CallService", "super.onCallAdded error: ${e.message}")
        }
        
        // --- SMART BLUETOOTH AUTOROUTING (Phase 10) ---
        // Android often defaults to earpiece. We force BT if available.
        try {
            val audioState = callAudioState
            if (audioState != null && (audioState.supportedRouteMask and CallAudioState.ROUTE_BLUETOOTH) != 0) {
                // If a connection exists, aggressively route to it
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
                    val activeBt = audioState.activeBluetoothDevice
                    if (activeBt != null) {
                        requestBluetoothAudio(activeBt)
                    } else if (audioState.supportedBluetoothDevices.isNotEmpty()) {
                        // Just pick the first connected one
                        requestBluetoothAudio(audioState.supportedBluetoothDevices.first())
                    } else {
                        setAudioRoute(CallAudioState.ROUTE_BLUETOOTH)
                    }
                } else {
                    setAudioRoute(CallAudioState.ROUTE_BLUETOOTH)
                }
            }
        } catch (e: Exception) {
            Log.e("CallService", "BT Auto-Route failed: ${e.message}")
        }
        
        Log.d("CallService", "onCallAdded: ID=${call.details.handle} State=${call.state}")
        val isFirstCall = calls.isEmpty()
        
        // ADD TO LIST
        if (!calls.contains(call)) {
             calls.add(call)

        }
        
        
        activeCall = call
        lastKnownCall = call
        
        // ANDROID 14 CRITICAL: PROPER Foreground Promotion
        // Use showNotification to build a fully compliant CallStyle notification immediately
        try {
             showNotification(call)

        } catch (e: Exception) {
             Log.e("CallService", "Immediate showNotification failed: ${e.message}")
        }
        
        // Auto-launch UI
        // Auto-launch UI
        try {

            /*
            val intent = Intent(this, MainActivity::class.java)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            startActivity(intent)
            */

        } catch (e: Exception) {
            Log.e("CallService", "Error launching UI: ${e.message}")
        }
        
        // Register callbacks with FULL try-catch protection
        call.registerCallback(object : Call.Callback() {
            override fun onStateChanged(call: Call, state: Int) {
                try {
                    if (state == Call.STATE_DISCONNECTED) {
                        // IMMEDIATE cleanup on full disconnect.
                        // Don't clean up on DISCONNECTING — call is still alive.
                        Log.d("CallService", "Call state -> DISCONNECTED. Killing notification.")
                        calls.remove(call)
                        if (calls.isEmpty()) {
                            killNotification()
                            activeCall = null
                        } else {
                            activeCall = calls.lastOrNull()
                            activeCall?.let { showNotification(it) }
                        }
                        try {
                            // FAST NATIVE CAMERA KILL: 
                            // Ensure the physical lens turns off immediately upon hangup, 
                            // even before the Flutter UI processes the disconnect event.
                            call.videoCall?.setCamera(null)
                        } catch (e: Exception) {
                            Log.e("CallService", "Failed to clear camera on disconnect: ${e.message}")
                        }
                        
                        // Unregister this callback to prevent stale events
                        try { call.unregisterCallback(this) } catch (_: Exception) {}
                    } else if (state != Call.STATE_DISCONNECTING) {
                        // Update notification for all states EXCEPT disconnect-related
                        showNotification(call)
                    }
                    broadcastCallState()
                } catch (e: Exception) {
                    Log.e("CallService", "onStateChanged error: ${e.message}")
                }
            }
            
            override fun onDetailsChanged(call: Call, details: Call.Details) {
                try {
                    super.onDetailsChanged(call, details)
                    if (call.videoCall != null) {
                         registerVideoCallback(call.videoCall)
                    }
                } catch (e: Exception) {
                    Log.e("CallService", "onDetailsChanged error: ${e.message}")
                }
            }

            override fun onConferenceableCallsChanged(call: Call, conferenceableCalls: MutableList<Call>?) {
                try {
                    super.onConferenceableCallsChanged(call, conferenceableCalls)
                } catch (e: Exception) {
                    Log.e("CallService", "onConferenceableCallsChanged error: ${e.message}")
                }
            }

            override fun onVideoCallChanged(call: Call, videoCall: InCallService.VideoCall?) {
                try {
                    super.onVideoCallChanged(call, videoCall)
                    Log.d("CallService", "VideoCall Object CHANGED: ${videoCall.hashCode()}")
                    if (videoCall != null) {
                        registerVideoCallback(videoCall)
                    }
                } catch (e: Exception) {
                    Log.e("CallService", "onVideoCallChanged error: ${e.message}")
                }
            }
        })
        
        try {
            if (call.videoCall != null) {
                registerVideoCallback(call.videoCall)
            }
        } catch (e: Exception) {
            Log.e("CallService", "registerVideoCallback error: ${e.message}")
        }
        
        // Removed duplicate showNotification — already called at line 571
        // (calling it twice could cause notification dedup issues on some devices)
        
        // NOTIFY FLUTTER
        try {
            val callName = call.details.callerDisplayName ?: ""
            val callNumber = call.details.handle?.schemeSpecificPart ?: "Unknown"
            val callData = hashMapOf<String, Any?>(
                "name" to callName,
                "number" to callNumber,
                "isIncoming" to (call.state == Call.STATE_RINGING)
            )
            MainActivity.instance?.sendEvent("incomingCall", callData)
            
            // CRITICAL IN-APP ROUTING: 
            if (call.state == Call.STATE_RINGING) {
                val isScreenOn = getSystemService(android.os.PowerManager::class.java)?.isInteractive == true
                val canDrawOverlays = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) android.provider.Settings.canDrawOverlays(this) else true
                val isFlutterAlive = MainActivity.eventSink != null
                
                // If screen is on, unlocked, and we can draw overlays, DO NOT force full screen app!
                // Let the Flutter 'NeuralPulseOverlay' handle the incoming banner!
                if (!MainActivity.isAppVisible && isScreenOn && canDrawOverlays && isFlutterAlive) {
                     Log.d("CallService", "Delegating incoming banner to Dynamic Island Overlay")
                     broadcastCallState()
                } else {
                     // Phone locked, or no overlay permission. Force Full Screen UI!
                     val intent = Intent(this, MainActivity::class.java).apply {
                         addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                         putExtra("incoming_call", true)
                     }
                     startActivity(intent)
                }
            }
        } catch (e: Exception) {
            Log.e("CallService", "Failed to send incomingCall event: ${e.message}")
        }
        
        broadcastCallState()
    }

    private var currentVideoCall: InCallService.VideoCall? = null
    
    // Define callback once to hold reference
    private val videoCallback = object : InCallService.VideoCall.Callback() {
        override fun onSessionModifyRequestReceived(videoProfile: VideoProfile) {
            val requestedState = videoProfile.videoState
            Log.d("CallService", "📹 Session Modify Request: State=$requestedState")

            if (VideoProfile.isVideo(requestedState)) {
                // CASE 1: UPGRADE REQUEST (Show UI + Popup)
                Log.d("CallService", "Case: UPGRADE to Video")
                
                // Send Event to Flutter (IMMEDIATE)
                MainActivity.instance?.sendEvent("incomingVideoRequest", null)
                
            } else {
                // CASE 2: DOWNGRADE TO AUDIO (Silent Switch)
                Log.d("CallService", "Case: DOWNGRADE to Audio - Auto Accepting")
                
                // CRITICAL FIX: We MUST respond to the framework or the session gets stuck!
                try {
                     // Accept the downgrade request by echoing the requested profile
                     // Use activeCall?.videoCall to ensure we use the LATEST object, not a cached one
                     activeCall?.videoCall?.sendSessionModifyResponse(videoProfile) 
                     Log.d("CallService", "✅ Auto-Accepted Downgrade via activeCall")
                } catch (e: Exception) {
                     Log.e("CallService", "Auto-Accept Fail: ${e.message}")
                }

                MainActivity.instance?.sendEvent("downgradeToAudio", null)
            }
        }
        override fun onCallDataUsageChanged(dataUsage: Long) {}
        override fun onCameraCapabilitiesChanged(cameraCapabilities: android.telecom.VideoProfile.CameraCapabilities) {}
        override fun onCallSessionEvent(event: Int) {}
        override fun onPeerDimensionsChanged(width: Int, height: Int) {}
        override fun onVideoQualityChanged(videoQuality: Int) {}
        override fun onSessionModifyResponseReceived(status: Int, requestedProfile: VideoProfile?, responseProfile: VideoProfile?) {}
    }

    private fun registerVideoCallback(videoCall: InCallService.VideoCall?) {
        // 1. Unregister Old (Logic handled by overwriting or new instance)
        if (currentVideoCall != null && currentVideoCall != videoCall) {
            try {
                 currentVideoCall?.unregisterCallback(videoCallback)
            } catch (e: Exception) {}
        }
        
        // 2. Register New
        if (videoCall != null) {
            currentVideoCall = videoCall
            try {
                videoCall.registerCallback(videoCallback)
                Log.d("CallService", "✅ Video Callback Registered")
            } catch (e: Exception) {
                Log.e("CallService", "Callback Reg Error: ${e.message}")
            }
        }
    }

    override fun onCallRemoved(call: Call) {
        // SECONDARY CAMERA KILL (Fallback): 
        // Guarantee the telecom hook to the camera is destroyed when the object is garbage collected
        try {
            call.videoCall?.setCamera(null)
        } catch (e: Exception) {}
        
        // CRITICAL: Let the Telecom framework clean up its internal state first.
        try {
            super.onCallRemoved(call)
        } catch (e: Exception) {
            Log.e("CallService", "super.onCallRemoved error: ${e.message}")
        }

        try {
            calls.remove(call) // Idempotent if already removed by onStateChanged
            
            if (calls.isEmpty()) {
                killNotification()
                activeCall = null
                serviceInstance = null
            } else {
                activeCall = calls.lastOrNull()
                activeCall?.let { showNotification(it) }
            }
            broadcastCallState()
        } catch (e: Exception) {
            Log.e("CallService", "onCallRemoved error: ${e.message}")
        }
    }
}
