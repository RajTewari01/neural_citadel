package com.example.neural_citadel

import android.content.Context
import android.view.View
import android.widget.FrameLayout
import android.view.TextureView
import android.graphics.SurfaceTexture
import android.view.Surface
import android.telecom.Call
import android.telecom.VideoProfile
import android.view.Gravity
import android.hardware.camera2.CameraManager
import android.telecom.InCallService
import android.view.MotionEvent
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import io.flutter.plugin.platform.PlatformView
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.BinaryMessenger

class NeuralVideoView(context: Context, messenger: BinaryMessenger, id: Int) : PlatformView, MethodChannel.MethodCallHandler, TextureView.SurfaceTextureListener {
    
    private val channel: MethodChannel = MethodChannel(messenger, "neural_video_view_$id")
    private val container: FrameLayout = FrameLayout(context)
    
    // Surfaces
    private var remoteView: TextureView
    private var localView: TextureView
    private var remoteSurface: Surface? = null
    private var localSurface: Surface? = null
    
    // State
    private var videoCall: InCallService.VideoCall? = null
    private var isFrontCamera = true
    private var isSwapped = false // True = Local Big, Remote Small
    private var isPaused = false // NEW: Track Pause State
    
    // Drag State
    private var lastX = 0f
    private var lastY = 0f
    private var dX = 0f
    private var dY = 0f
    private var startClickTime: Long = 0
    private var isHidden = false // Used for PiP exiting
    
    // Persist Position
    private var customX: Float? = null
    private var customY: Float? = null

    // Dedicated Video Callback for Session Events
    private val videoCallback = object : InCallService.VideoCall.Callback() {
         override fun onSessionModifyResponseReceived(status: Int, requestedProfile: VideoProfile?, responseProfile: VideoProfile?) {
              if (status == android.telecom.Connection.VideoProvider.SESSION_MODIFY_REQUEST_SUCCESS) {
                   container.post { initializeVideoIfReady() }
              }
         }
         // Must override abstract methods
         override fun onCallDataUsageChanged(dataUsage: Long) {}
         override fun onCameraCapabilitiesChanged(cameraCapabilities: android.telecom.VideoProfile.CameraCapabilities) {}
         override fun onCallSessionEvent(event: Int) {}
         override fun onPeerDimensionsChanged(width: Int, height: Int) {}
         override fun onVideoQualityChanged(videoQuality: Int) {}
         override fun onSessionModifyRequestReceived(videoProfile: VideoProfile) {}
    }

    init {
        channel.setMethodCallHandler(this)
        
        // 1. Remote View (Caller Video)
        remoteView = TextureView(context)
        remoteView.surfaceTextureListener = this
        container.addView(remoteView)
        
        // 2. Local View (My Face)
        localView = TextureView(context)
        localView.surfaceTextureListener = object : TextureView.SurfaceTextureListener {
             override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height: Int) {
                 localSurface = Surface(surface)
                 initializeVideoIfReady()
             }
             override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) {}
             override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean {
                 localSurface?.release()
                 localSurface = null
                 return true
             }
             override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
        }
        container.addView(localView)
        
        // Initial Layout
        updateLayouts()

        // Hook into active call
        CallService.activeCall?.let {
            videoCall = it.videoCall
            
            // 1. Listen for Provider Changes (Call.Callback)
            it.registerCallback(object : Call.Callback() {
                 override fun onVideoCallChanged(call: Call, vc: InCallService.VideoCall?) {
                      super.onVideoCallChanged(call, vc)
                      videoCall = vc
                      initializeVideoIfReady() // Re-attach surfaces to new provider
                 }
                 override fun onStateChanged(call: Call, state: Int) {}
            })
            initializeVideoIfReady()
        }
        
        // RESPONSIVE LAYOUT (Auto-Detect Container Resize)
        container.addOnLayoutChangeListener { _, _, _, _, _, _, _, _, _ ->
             if (!isHidden) updateLayouts()
        }
    }

    private fun updateLayouts() {
        val totalW = container.width
        val totalH = container.height
        // Safety check
        if (totalW == 0 || totalH == 0) return 

        val scale = container.context.resources.displayMetrics.density
        val bigView = if (isSwapped) localView else remoteView
        val smallView = if (isSwapped) remoteView else localView

        // ----------------------------------------------------
        // 1. BIG VIEW (3:4 Portrait, Top Aligned)
        // ----------------------------------------------------
        // Height = Width * 1.33 (3:4 Portrait Ratio) - Matches User Request for "Half Screen / Hold Call Area"
        val bigH = (totalW * 1.33).toInt() 
        
        val bigParams = FrameLayout.LayoutParams(totalW, bigH).apply {
            gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
            setMargins(0, 0, 0, 0)
        }
        bigView.layoutParams = bigParams
        bigView.elevation = 0f
        bigView.outlineProvider = null // Reset corners
        bigView.clipToOutline = false
        bigView.background = null // Remove borders
        bigView.translationX = 0f
        bigView.translationY = 0f
        
        // Clear touch listeners on Big View
        bigView.setOnTouchListener(null)
        bigView.bringToFront() // Ensure z-index logic if needed, but small view should be highest
        
        // ----------------------------------------------------
        // 2. SMALL VIEW (Draggable PiP)
        // ----------------------------------------------------
        // Size: 120dp x 160dp (Portrait Ratio for PiP)
        val smallW = (100 * scale).toInt()
        val smallH = (133 * scale).toInt() // 4:3 Portrait roughly
        
        val smallParams = FrameLayout.LayoutParams(smallW, smallH)
        smallParams.gravity = Gravity.TOP or Gravity.START // Anchor Top-Left so translation works
        smallParams.setMargins(0, 0, 0, 0) // No margins, pure translation

        smallView.layoutParams = smallParams
        smallView.elevation = 20f * scale
        
        // Restore Position
        if (customX != null && customY != null) {
             val maxX = (totalW - smallW).toFloat()
             val maxY = (totalH - smallH).toFloat()
             smallView.translationX = customX!!.coerceIn(0f, maxX)
             smallView.translationY = customY!!.coerceIn(0f, maxY)
        } else {
             // Default: Top Right
             smallView.translationX = (totalW - smallW - 16 * scale)
             smallView.translationY = (50 * scale)
             customX = smallView.translationX
             customY = smallView.translationY
        }
        
        // GLASSMORPHISM Styling
        smallView.outlineProvider = object : android.view.ViewOutlineProvider() {
            override fun getOutline(view: View, outline: android.graphics.Outline) {
                outline.setRoundRect(0, 0, view.width, view.height, 16 * scale)
            }
        }
        smallView.clipToOutline = true
        
        // Glass Border (20% White)
        val border = GradientDrawable().apply {
             cornerRadius = 16 * scale
             setStroke((1 * scale).toInt(), Color.argb(51, 255, 255, 255)) // 20% White
             setColor(Color.BLACK) // Background for video (safeguard)
        }
        // Small View needs a container? TextureView doesn't support background drawable well sometimes.
        // But let's try setting background on the view itself.
        // NOTE: TextureView is transparent by default, displaying surface content.
        // Background drawable renders BEHIND content. Border stroke renders?
        // Actually, TextureView doesn't support background/borders easily. 
        // We might need a wrapper, but let's assume PlatformView FrameLayout wrapper can be modified? 
        // No, we are adding TextureViews directly.
        // Alternative: Use a sibling View for the border overlaid on top?
        // Complexity: High. 
        // Simple Fix: TextureView `elevation` handles shadow. Round rect handled by outline.
        // Border: We can't easily draw a border on TextureView without a wrapper.
        // Since we want premium, let's just stick to Round Rect + Elevation (Shadow) for now.
        // It provides the "Glass" shape. The border is nice but TextureView limits us.

        smallView.bringToFront()
        
        // TOUCH LISTENER (Drag + Click)
        smallView.setOnTouchListener { view, event ->
             when (event.action) {
                 MotionEvent.ACTION_DOWN -> {
                     lastX = event.rawX
                     lastY = event.rawY
                     dX = view.translationX
                     dY = view.translationY
                     startClickTime = System.currentTimeMillis()
                     true
                 }
                 MotionEvent.ACTION_MOVE -> {
                     val deltaX = event.rawX - lastX
                     val deltaY = event.rawY - lastY
                     
                     val newX = dX + deltaX
                     val newY = dY + deltaY
                     
                     // Bounds Check (Restrict to Top 4:3 Area)
                     val parentW = (view.parent as View).width
                     val parentH = (view.parent as View).height
                     
                     // 4:3 Limit Height (Actually 3:4 Portrait now)
                     val limitH = (parentW * 1.33).toFloat()
                     
                     val safeX = newX.coerceIn(0f, (parentW - view.width).toFloat())
                     val safeY = newY.coerceIn(0f, (limitH - view.height).toFloat())
                     
                     view.translationX = safeX
                     view.translationY = safeY
                     
                     // Update custom pos
                     customX = safeX
                     customY = safeY
                     true
                 }
                 MotionEvent.ACTION_UP -> {
                     val clickDuration = System.currentTimeMillis() - startClickTime
                     val traveled = Math.hypot((event.rawX - lastX).toDouble(), (event.rawY - lastY).toDouble())
                     
                     if (clickDuration < 200 && traveled < 10) {
                         // CLICK DETECTED -> SWAP
                         handleSwap()
                     }
                     true
                 }
                 else -> false
             }
        }
    }

    private fun handleSwap() {
        android.util.Log.d("NeuralVideo", "🔄 Swapping Views")
        isSwapped = !isSwapped
        
        // Haptic Feedback
        container.performHapticFeedback(android.view.HapticFeedbackConstants.LONG_PRESS)
        
        updateLayouts()
        
        // Force refresh to ensure surface order renders correctly
        initializeVideoIfReady()
    }

    private fun initializeVideoIfReady() {
        // PERMISSION CHECK
        if (container.context.checkSelfPermission(android.Manifest.permission.CAMERA) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            android.util.Log.e("NeuralVideo", "Camera permission missing in Native View")
            return
        }

        // PAUSE CHECK: Do not initialize if manually paused
        if (isPaused) {
            android.util.Log.d("NeuralVideo", "Skipping init - Camera is PAUSED")
            return
        }

        val activeVC = CallService.activeCall?.videoCall ?: videoCall
        
        if (remoteSurface != null && localSurface != null && activeVC != null) {
            try {
                // 1. Find Correct Camera ID
                val targetId = getCameraId(container.context, isFrontCamera) ?: "1"
                
                // 2. FORCE REFRESH: Set Null then Set Real
                // This seems to be the only way to reliably "wake up" the surfaces on some devices
                activeVC.setCamera(null) 
                activeVC.setPreviewSurface(null)
                
                // 3. Wait for driver release (Async)
                container.postDelayed({
                    try {
                        // Double check pause state before async execution
                        if (isPaused) return@postDelayed

                        activeVC.setCamera(targetId)
                        activeVC.setPreviewSurface(localSurface)
                        activeVC.setDisplaySurface(remoteSurface)
                        
                        // 4. Removed Auto-Upgrade: We do NOT want to force video 
                        // just because the UI component was loaded. Upgrades are now explicit.
                        
                        // 5. Force Speaker
                        CallService.setSpeaker(true)
                        
                        // 6. Register
                        activeVC.registerCallback(videoCallback)
                        videoCall = activeVC
                        
                    } catch (e: Exception) {
                        android.util.Log.e("NeuralVideo", "Async Cam Init Failed: ${e.message}")
                    }
                }, 100) 
                
            } catch (e: Exception) {
                android.util.Log.e("NeuralVideo", "Init Error: ${e.message}")
            }
        }
    }

    // Robust Camera ID Finding
    private fun getCameraId(context: Context, front: Boolean): String? {
        try {
            val manager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
            for (id in manager.cameraIdList) {
                val characteristics = manager.getCameraCharacteristics(id)
                val facing = characteristics.get(android.hardware.camera2.CameraCharacteristics.LENS_FACING)
                if (front && facing == android.hardware.camera2.CameraCharacteristics.LENS_FACING_FRONT) return id
                if (!front && facing == android.hardware.camera2.CameraCharacteristics.LENS_FACING_BACK) return id
            }
        } catch (e: Exception) {}
        return if (front) "1" else "0"
    }

    companion object {
        var instance: NeuralVideoView? = null
    }

    init {
        instance = this // Track active view
        container.setBackgroundColor(Color.BLACK)
        
        // 1. ADD LOCAL VIEW (TextureView)
        // ... (existing init code is fine, but we are inside init block here implicitly)
        
        // RESPONSIVE LAYOUT (Auto-Detect Container Resize)
        container.addOnLayoutChangeListener { _, _, _, _, _, _, _, _, _ ->
             if (!isHidden) updateLayouts()
        }
    }
    
    // PUBLIC ACTIONS (Called from MainActivity)
    fun switchCamera() {
        isFrontCamera = !isFrontCamera
        // If paused, just toggle the flag but don't init
        if (!isPaused) {
            initializeVideoIfReady()
        }
    }

    fun pauseCamera() {
        isPaused = true
        videoCall?.setCamera(null)
        videoCall?.setPreviewSurface(null)
    }

    fun resumeCamera() {
        isPaused = false
        initializeVideoIfReady()
    }
    
    fun setPipMode(active: Boolean) {
        isHidden = active
        if (active) {
            localView.visibility = View.GONE
            val params = FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT)
            remoteView.layoutParams = params
            remoteView.translationX = 0f
            remoteView.translationY = 0f
        } else {
            localView.visibility = View.VISIBLE
            updateLayouts()
        }
    }

    override fun getView(): View {
        return container
    }

    override fun dispose() {
        if (instance == this) instance = null
        try {
            videoCall?.setCamera(null) // CRITICAL FIX: Turn off physical camera lens
            videoCall?.setDisplaySurface(null)
            videoCall?.setPreviewSurface(null)
        } catch (e: Exception) {
            android.util.Log.e("NeuralVideo", "Dispose Error: ${e.message}")
        }
        remoteSurface?.release()
        localSurface?.release()
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "switchCamera" -> {
                switchCamera()
                result.success(null)
            }
            "pauseCamera" -> {
                pauseCamera()
                result.success(null)
            }
            "resumeCamera" -> {
                resumeCamera()
                result.success(null)
            }
            "setPipMode" -> {
                val active = call.argument<Boolean>("active") ?: false
                setPipMode(active)
                result.success(null)
            }
            "initialize" -> {
                 initializeVideoIfReady()
                 result.success(null)
            }
            else -> result.notImplemented()
        }
    }

    // Remote Surface Listener
    override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height: Int) {
        remoteSurface = Surface(surface)
        initializeVideoIfReady()
    }
    override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) {}
    override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean {
        remoteSurface?.release()
        remoteSurface = null
        return true
    }
    override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
}
