# 📱 Mobile Citadel Setup Guide

## 1. Install Flutter (The Engine)
1.  Download the **Flutter SDK** from [flutter.dev](https://docs.flutter.dev/get-started/install/windows).
2.  Extract the zip file to `C:\src\flutter` (Create folder if needed).
3.  Add `C:\src\flutter\bin` to your **Environment Variables Path**.
    *   Wait, I can run a script to check this for you later!

## 2. Enable Developer Mode on Phone
1.  Go to Settings -> About Phone.
2.  Tap **Build Number** 7 times.
3.  Go to Developer Options -> Enable **USB Debugging**.
4.  Plug phone into PC via USB.

## 3. Run the App
Open a terminal in this folder (`d:\neural_citadel\apps\mobile_citadel`) and run:
`flutter run`

---
**Note:** The app will ask for your **Server IP**. 
Run `ipconfig` in terminal to find your PC's IP (usually `192.168.x.x`).
