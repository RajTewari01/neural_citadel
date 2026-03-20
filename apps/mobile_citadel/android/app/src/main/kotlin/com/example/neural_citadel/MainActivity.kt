package com.example.neural_citadel

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.content.Intent
import android.telecom.TelecomManager
import android.net.Uri
import android.content.pm.ShortcutManager
import android.content.pm.ShortcutInfo
import android.graphics.drawable.Icon
import android.os.Build

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.neuralcitadel/native"
    private var proximityWakeLock: android.os.PowerManager.WakeLock? = null
    
    companion object {
        var instance: MainActivity? = null
        var isAppVisible: Boolean = false
        var eventSink: io.flutter.plugin.common.EventChannel.EventSink? = null
    }

    override fun onCreate(savedInstanceState: android.os.Bundle?) {
        super.onCreate(savedInstanceState)
        instance = this
        handleLockScreen()
        
        // PROXIMITY SENSOR: Turn screen off when near ear
        val powerManager = getSystemService(android.os.PowerManager::class.java)
        if (powerManager.isWakeLockLevelSupported(android.os.PowerManager.PROXIMITY_SCREEN_OFF_WAKE_LOCK)) {
            proximityWakeLock = powerManager.newWakeLock(
                android.os.PowerManager.PROXIMITY_SCREEN_OFF_WAKE_LOCK,
                "com.neuralcitadel:Proximity"
            )
        }
    }

    override fun onResume() {
        super.onResume()
        isAppVisible = true
    }

    override fun onPause() {
        super.onPause()
        isAppVisible = false
    }

    override fun onDestroy() {
        if (proximityWakeLock?.isHeld == true) {
            proximityWakeLock?.release()
        }
        if (instance == this) { instance = null }
        super.onDestroy()
    }
    
    // ----------------------------------------------------------------
    // PICTURE-IN-PICTURE (PiP) SUPPORT
    // ----------------------------------------------------------------
    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        // Auto-enter PiP if we have an active VIDEO call
        val c = CallService.activeCall
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && c != null) {
            val isVideo = (c.details.videoState == android.telecom.VideoProfile.STATE_BIDIRECTIONAL ||
                          c.details.videoState == android.telecom.VideoProfile.STATE_RX_ENABLED ||
                          c.details.videoState == android.telecom.VideoProfile.STATE_TX_ENABLED)
            
            if (isVideo) {
                enterPictureInPicture()
            }
        }
    }
    
    private fun enterPictureInPicture() {
         if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
             try {
                // Match Portrait Video Ratio (3:4) for consistent framing
                val aspectRatio = android.util.Rational(3, 4)
                val params = android.app.PictureInPictureParams.Builder()
                    .setAspectRatio(aspectRatio)
                    .build()
                enterPictureInPictureMode(params)
             } catch (e: Exception) {
                 android.util.Log.e("NeuralNative", "PiP Failed: ${e.message}")
             }
         }
    }

    override fun onPictureInPictureModeChanged(isInPictureInPictureMode: Boolean, newConfig: android.content.res.Configuration) {
        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig)
        if (isInPictureInPictureMode) {
             // Notify Flutter: HIDE UI
             sendEvent("PIP_MODE_CHANGED", true)
        } else {
             // Notify Flutter: SHOW UI
             sendEvent("PIP_MODE_CHANGED", false)
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent) // Ensure Flutter gets the updated intent
        
        // CRITICAL IN-APP ROUTING: 
        // Wakes up Flutter UI if CallService fired a new intent while app is in foreground
        if (intent.getBooleanExtra("incoming_call", false)) {
            val call = CallService.activeCall
            if (call != null && call.state == android.telecom.Call.STATE_RINGING) {
                val callName = call.details.callerDisplayName ?: ""
                val callNumber = call.details.handle?.schemeSpecificPart ?: "Unknown"
                val callData = hashMapOf<String, Any?>(
                    "name" to callName,
                    "number" to callNumber,
                    "isIncoming" to true
                )
                sendEvent("incomingCall", callData)
            }
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        // RE-REGISTER VIDEO FACTORY
        flutterEngine
            .platformViewsController
            .registry
            .registerViewFactory("neural_video_view", NeuralVideoFactory(flutterEngine.dartExecutor.binaryMessenger))
            
        // CALL STATE EVENT CHANNEL
        io.flutter.plugin.common.EventChannel(flutterEngine.dartExecutor.binaryMessenger, "com.neuralcitadel/callStateStream").setStreamHandler(
            object : io.flutter.plugin.common.EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: io.flutter.plugin.common.EventChannel.EventSink?) {
                    eventSink = events
                    // Send initial state
                    val active = CallService.activeCall
                    if (active != null) {
                        events?.success(mapOf("event" to "state_sync", "data" to CallService.getAllCallsState()))
                    }
                }

                override fun onCancel(arguments: Any?) {
                    eventSink = null
                }
            }
        )
            
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "setDefaultDialer") {
                try {
                    if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
                        val roleManager = getSystemService(android.app.role.RoleManager::class.java)
                        if (roleManager.isRoleAvailable(android.app.role.RoleManager.ROLE_DIALER)) {
                            if (roleManager.isRoleHeld(android.app.role.RoleManager.ROLE_DIALER)) {
                                result.success(true) // Already held
                            } else {
                                val intent = roleManager.createRequestRoleIntent(android.app.role.RoleManager.ROLE_DIALER)
                                startActivityForResult(intent, 123)
                                result.success(true)
                            }
                        } else {
                            // Fallback if role unavailable
                            val intent = Intent(TelecomManager.ACTION_CHANGE_DEFAULT_DIALER)
                            intent.putExtra(TelecomManager.EXTRA_CHANGE_DEFAULT_DIALER_PACKAGE_NAME, packageName)
                            startActivity(intent)
                            result.success(true)
                        }
                    } else {
                        val intent = Intent(TelecomManager.ACTION_CHANGE_DEFAULT_DIALER)
                        intent.putExtra(TelecomManager.EXTRA_CHANGE_DEFAULT_DIALER_PACKAGE_NAME, packageName)
                        startActivity(intent)
                        result.success(true)
                    }
                } catch (e: Exception) {
                    result.error("UNAVAILABLE", "Could not launch intent: ${e.message}", null)
                }
            } else if (call.method == "switchCamera") {
                // Forward to Active Video View
                val view = NeuralVideoView.instance
                if (view != null) {
                    view.switchCamera()
                    result.success(null)
                } else {
                    result.error("NO_VIDEO_VIEW", "No active video view found", null)
                }
            } else if (call.method == "upgradeToVideo") {
                try {
                     val vc = CallService.activeCall?.videoCall
                     if (vc != null) {
                         val videoProfile = android.telecom.VideoProfile(android.telecom.VideoProfile.STATE_BIDIRECTIONAL)
                         vc.sendSessionModifyRequest(videoProfile)
                         result.success(true)
                     } else {
                         result.error("NO_VIDEO_CALL", "Video call object missing", null)
                     }
                } catch (e: Exception) {
                     result.error("ERROR", "Upgrade failed: ${e.message}", null)
                }
            } else if (call.method == "downgradeToAudio") {
                try {
                     val vc = CallService.activeCall?.videoCall
                     if (vc != null) {
                         val videoProfile = android.telecom.VideoProfile(android.telecom.VideoProfile.STATE_AUDIO_ONLY)
                         vc.sendSessionModifyRequest(videoProfile)
                         result.success(true)
                     } else {
                         result.error("NO_VIDEO_CALL", "Video call object missing", null)
                     }
                } catch (e: Exception) {
                     result.error("ERROR", "Downgrade failed: ${e.message}", null)
                }
            } else if (call.method == "acceptVideoUpgrade") {
                try {
                     val vc = CallService.activeCall?.videoCall
                     if (vc != null) {
                         val videoProfile = android.telecom.VideoProfile(android.telecom.VideoProfile.STATE_BIDIRECTIONAL)
                         vc.sendSessionModifyResponse(videoProfile)
                         
                         // Re-initialize local video view immediately since we accepted
                         NeuralVideoView.instance?.resumeCamera()
                         result.success(true)
                     } else {
                         result.error("NO_VIDEO_CALL", "Video call object missing", null)
                     }
                } catch (e: Exception) {
                     result.error("ERROR", "Accept Video failed: ${e.message}", null)
                }
            } else if (call.method == "pauseCamera") {
                val view = NeuralVideoView.instance
                if (view != null) {
                    view.pauseCamera()
                    result.success(null)
                } else {
                    result.success(null) // Fail silently
                }
            } else if (call.method == "resumeCamera") {
                val view = NeuralVideoView.instance
                if (view != null) {
                    view.resumeCamera()
                    result.success(null)
                } else {
                    result.success(null)
                }
            } else if (call.method == "shareText") {
                val text = call.argument<String>("text")
                if (text != null) {
                    val sendIntent = Intent().apply {
                        action = Intent.ACTION_SEND
                        putExtra(Intent.EXTRA_TEXT, text)
                        type = "text/plain"
                    }
                    val shareIntent = Intent.createChooser(sendIntent, null).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    startActivity(shareIntent)
                    result.success(true)
                } else {
                    result.error("INVALID", "Text missing", null)
                }
            } else if (call.method == "checkActiveCall") {
                // NEW HYBRID CONTRACT
                val state = CallService.getAllCallsState()
                android.util.Log.e("NeuralNative", "checkActiveCall: state size=${state.size}, content=$state")
                if (state.isNotEmpty()) {
                    result.success(state)
                } else {
                    android.util.Log.e("NeuralNative", "checkActiveCall: Returning NULL to Flutter")
                    // VISUAL DEBUG: REMOVED (User Feedback)
                    // android.os.Handler(android.os.Looper.getMainLooper()).post {
                    //      android.widget.Toast.makeText(this@MainActivity, "Native: State Empty!", android.widget.Toast.LENGTH_SHORT).show()
                    // }
                    result.success(null)
                }
            } else if (call.method == "launchApp") {
                val pkg = call.argument<String>("package")
                if (pkg != null) {
                    try {
                       val intent = packageManager.getLaunchIntentForPackage(pkg)
                       if (intent != null) {
                           intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                           startActivity(intent)
                           result.success(true)
                       } else {
                           result.error("NOT_FOUND", "App not installed", null)
                       }
                    } catch (e: Exception) {
                       result.error("ERROR", e.message, null)
                    }
                } else {
                    result.error("INVALID", "Package name missing", null)
                }
            } else if (call.method == "bringToFront") {
                try {
                    val intent = Intent(context, MainActivity::class.java)
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
                    startActivity(intent)
                    result.success(true)
                } catch (e: Exception) {
                     result.error("ERROR", e.message, null)
                }
            } else if (call.method == "answerCall") {
                val c = CallService.activeCall
                if (c != null) {
                    c.answer(0) // VideoProfile.STATE_AUDIO_ONLY
                    result.success(true)
                } else {
                    result.error("NO_CALL", "No active call found", null)
                }
            } else if (call.method == "endCall") {
                val c = CallService.activeCall
                if (c != null) {
                    // Check API level if needed, usually just disconnect() or reject()
                    if (c.state == android.telecom.Call.STATE_RINGING) {
                        c.reject(false, null)
                    } else {
                        c.disconnect()
                    }
                    result.success(true)
                } else {
                    result.error("NO_CALL", "No active call found", null)
                }
            } else if (call.method == "toggleHold") {
                val on = call.argument<Boolean>("active") ?: false
                CallService.toggleHold(on)
                result.success(true)
            } else if (call.method == "toggleMute") {
                val on = call.argument<Boolean>("active") ?: false
                CallService.setMute(on)
                result.success(true)
            } else if (call.method == "toggleSpeaker") {
                val on = call.argument<Boolean>("active") ?: false
                CallService.setSpeaker(on)
                result.success(true)
            } else if (call.method == "setAudioRoute") {
                val route = call.argument<Int>("route")
                if (route != null) {
                    CallService.setAudioRoute(route)
                    result.success(true)
                } else {
                    result.error("ERROR", "Route missing", null)
                }
            } else if (call.method == "setBluetoothAudioRoute") {
                val address = call.argument<String>("address")
                if (address != null) {
                    CallService.requestBluetoothAudio(address)
                    result.success(true)
                } else {
                    result.error("ERROR", "Bluetooth address missing", null)
                }
            } else if (call.method == "toggleRecording") {
                val on = call.argument<Boolean>("active") ?: false
                CallService.toggleRecording(on)
                result.success(true)
            } else if (call.method == "minimizeApp") {
                moveTaskToBack(true)
                result.success(true)
            } else if (call.method == "addCall") {
                try {
                    val intent = Intent(Intent.ACTION_DIAL)
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(intent)
                    result.success(true)
                } catch (e: Exception) {
                    result.error("ERROR", e.message, null)
                }
            } else if (call.method == "mergeCalls") {
                CallService.mergeCalls()
                result.success(true)
            } else if (call.method == "swapCalls") {
                CallService.swapCalls()
                result.success(true)
            } else if (call.method == "acceptVideoUpgrade") {
                CallService.acceptVideoUpgrade()
                result.success(true)
            } else if (call.method == "requestVideoUpgrade") {
                val c = CallService.activeCall
                if (c != null && android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
                    val videoProfile = android.telecom.VideoProfile(android.telecom.VideoProfile.STATE_BIDIRECTIONAL)
                    c.videoCall?.sendSessionModifyRequest(videoProfile)
                    result.success(true)
                } else {
                    result.error("UNSUPPORTED", "Video call not supported", null)
                }
            } else if (call.method == "downgradeToAudio") {
                val c = CallService.activeCall
                if (c != null && android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
                    val videoProfile = android.telecom.VideoProfile(android.telecom.VideoProfile.STATE_AUDIO_ONLY)
                    c.videoCall?.sendSessionModifyRequest(videoProfile)
                    result.success(true)
                } else {
                    result.error("UNSUPPORTED", "Video call not supported", null)
                }
            } else if (call.method == "placeCall") {
                val number = call.argument<String>("number")
                if (number != null) {
                    try {
                        val uri = Uri.fromParts("tel", number, null)
                        val intent = Intent(Intent.ACTION_CALL, uri)
                        if (checkSelfPermission(android.Manifest.permission.CALL_PHONE) == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                            startActivity(intent)
                            result.success(true)
                        } else {
                            result.error("PERMISSION", "CALL_PHONE denied", null)
                        }
                    } catch (e: Exception) {
                        result.error("ERROR", e.message, null)
                    }
                } else {
                    result.error("INVALID", "Number missing", null)
                }
            } else if (call.method == "createDirectCallShortcut") {
                val number = call.argument<String>("number")
                val name = call.argument<String>("name") ?: "Contact"
                
                if (number != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                     val shortcutManager = getSystemService(ShortcutManager::class.java)
                     if (shortcutManager.isRequestPinShortcutSupported) {
                         val intent = Intent(Intent.ACTION_CALL, Uri.parse("tel:$number"))
                         val shortcut = ShortcutInfo.Builder(context, "id_$number")
                             .setShortLabel(name)
                             .setIcon(Icon.createWithResource(context, R.mipmap.launcher_icon))
                             .setIntent(intent)
                             .build()
                         shortcutManager.requestPinShortcut(shortcut, null)
                         result.success(true)
                     } else {
                         result.error("UNSUPPORTED", "Not supported", null)
                     }
                } else {
                   result.success(false)
                }
            } else if (call.method == "placeVideoCall") {
                val number = call.argument<String>("number")
                if (number != null) {
                    try {
                        // 1. Google Meet / Duo Intent
                        val intent = Intent("com.google.android.apps.tachyon.action.CALL")
                        intent.data = Uri.parse("tel:$number")
                        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK

                        if (intent.resolveActivity(packageManager) != null) {
                             startActivity(intent)
                             result.success(true)
                        } else {
                             // 2. Generic Video Intent
                             val generic = Intent(Intent.ACTION_CALL)
                             generic.data = Uri.parse("tel:$number")
                             generic.putExtra("android.telecom.extra.START_CALL_WITH_VIDEO_STATE", 3) // Bidirectional
                             if (checkSelfPermission(android.Manifest.permission.CALL_PHONE) == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                                startActivity(generic)
                                result.success(true)
                             } else {
                                result.error("PERMISSION", "CALL_PHONE denied", null)
                             }
                        }
                    } catch (e: Exception) {
                        result.error("ERROR", e.message, null)
                    }
                } else {
                    result.error("INVALID", "Number missing", null)
                }
            } else if (call.method == "blockNumber") {
                 val number = call.argument<String>("number")
                 if (number != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                     try {
                         val values = android.content.ContentValues()
                         values.put(android.provider.BlockedNumberContract.BlockedNumbers.COLUMN_ORIGINAL_NUMBER, number)
                         contentResolver.insert(android.provider.BlockedNumberContract.BlockedNumbers.CONTENT_URI, values)
                         result.success(true)
                     } catch (e: Exception) {
                         result.error("ERROR", "Failed to block: ${e.message}", null)
                     }
                 } else {
                     result.error("UNSUPPORTED", "Requires Android N+", null)
                 }
            } else if (call.method == "unblockNumber") {
                 val number = call.argument<String>("number")
                 if (number != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                      try {
                          val deleted = contentResolver.delete(
                              android.provider.BlockedNumberContract.BlockedNumbers.CONTENT_URI,
                              "${android.provider.BlockedNumberContract.BlockedNumbers.COLUMN_ORIGINAL_NUMBER} = ?",
                              arrayOf(number)
                          )
                          result.success(deleted > 0)
                      } catch (e: Exception) {
                          result.error("ERROR", "Failed to unblock: ${e.message}", null)
                      }
                 } else {
                      result.error("UNSUPPORTED", "Requires Android N+", null)
                 }
            } else if (call.method == "shareText") {
                 val text = call.argument<String>("text")
                 if (text != null) {
                     try {
                         val sendIntent = Intent().apply {
                             action = Intent.ACTION_SEND
                             putExtra(Intent.EXTRA_TEXT, text)
                             type = "text/plain"
                         }
                         val shareIntent = Intent.createChooser(sendIntent, "Save Note to...")
                         shareIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                         startActivity(shareIntent)
                         result.success(true)
                     } catch (e: Exception) {
                         result.error("ERROR", e.message, null)
                     }
                 } else {
                      result.error("INVALID", "Text missing", null)
                 }
            } else if (call.method == "enableProximity") {
                 val enable = call.argument<Boolean>("enable") ?: false
                 try {
                     if (enable) {
                         if (proximityWakeLock?.isHeld == false) proximityWakeLock?.acquire()
                     } else {
                         if (proximityWakeLock?.isHeld == true) proximityWakeLock?.release()
                     }
                     result.success(true)
                 } catch (e: Exception) {
                     result.error("ERROR", e.message, null)
                 }
            } else if (call.method == "getBlockedNumbers") {
                 if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                     val list = ArrayList<String>()
                     try {
                         val cursor = contentResolver.query(
                             android.provider.BlockedNumberContract.BlockedNumbers.CONTENT_URI,
                             arrayOf(android.provider.BlockedNumberContract.BlockedNumbers.COLUMN_ORIGINAL_NUMBER),
                             null, null, null
                         )
                         cursor?.use {
                             while (it.moveToNext()) {
                                 list.add(it.getString(0))
                             }
                         }
                         result.success(list)
                     } catch (e: Exception) {
                         result.success(ArrayList<String>())
                     }
                 } else {
                     result.success(ArrayList<String>())
                 }
            } else if (call.method == "sendDtmf") {
                val key = call.argument<String>("key")
                if (key != null && key.isNotEmpty()) {
                    CallService.playDtmf(key[0])
                    result.success(true)
                } else {
                     result.error("INVALID", "Key missing", null)
                }
            } else if (call.method == "getAudioRoutes") {
                val routes = CallService.getAudioRoutes()
                if (routes.isNotEmpty()) {
                    result.success(routes)
                } else {
                    result.error("UNAVAILABLE", "Audio state not found", null)
                }
            } else if (call.method == "setAudioRoute") {
                val route = call.argument<Int>("route")
                if (route != null) {
                    CallService.setAudioRoute(route)
                    result.success(true)
                } else {
                    result.error("INVALID", "Route missing", null)
                }
            } else if (call.method == "createContact") {
                val number = call.argument<String>("number")
                if (number != null) {
                    CallService.createContact(number)
                    result.success(true)
                } else {
                    result.error("INVALID", "Number missing", null)
                }
            } else {
                result.notImplemented()
            }
        }
    }

    private fun handleLockScreen() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            val keyguardManager = getSystemService(android.app.KeyguardManager::class.java)
            keyguardManager?.requestDismissKeyguard(this, null)
        } else {
            window.addFlags(
                android.view.WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                android.view.WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                android.view.WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD or
                android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            )
        }
    }

    fun sendEvent(method: String, args: Any?) {
        runOnUiThread {
             flutterEngine?.dartExecutor?.binaryMessenger?.let {
                MethodChannel(it, CHANNEL).invokeMethod(method, args)
            }
        }
    }
}
