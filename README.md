# Voice Transcribe - Offline Speech-to-Text for Linux

🎤 A simple, offline voice transcription app for Ubuntu/Linux with system tray integration and global hotkey support.

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04-orange)

## Features

✅ **Completely Offline** - No internet required after setup  
✅ **Global Hotkeys** - Press F9 or Alt+. from any app to record (optional)  
✅ **System Tray Integration** - Runs quietly in the background  
✅ **Visual Feedback** - Color-coded status (Red/Green/Yellow)  
✅ **Auto Clipboard** - Transcribed text automatically copied  
✅ **No Notification Spam** - Silent operation, just color changes  
✅ **Lightweight** - Works on CPU-only systems (i5 8th gen tested)  

## Visual Status Indicators

🔴 **Red Circle** - Ready to record (click to start)  
🟢 **Green Circle** - Recording in progress (click to stop)  
🟡 **Yellow Circle** - Processing transcription  
🔴 **Red Circle** - Done! Text in clipboard, ready for next recording  

## Global Hotkeys (NEW in v1.1.0)

**Default Hotkeys:**
- **F9** - Primary hotkey (fast, single key)
- **Alt + .** - Secondary hotkey (works on laptop keyboards)

Both hotkeys toggle recording on/off from **anywhere** - even when other apps are in focus!

**Customize:** Right-click tray icon → Settings → Record new hotkeys  
**Optional:** Hotkeys are disabled by default, enable in Settings when ready

## Requirements

- Ubuntu 24.04 (or similar Debian-based distro with GNOME)
- ~500MB free disk space
- CPU: i5 8th gen or better recommended
- Microphone (external mic recommended for best accuracy)

## Quick Install

```bash
git clone https://github.com/YOUR_USERNAME/voice-transcribe.git
cd voice-transcribe
chmod +x install.sh
./install.sh
```

The installer will:
1. Install system dependencies (cmake, portaudio, etc.)
2. Install UV package manager (if not present)
3. Download and compile whisper.cpp
4. Download Whisper base model (~150MB)
5. Set up the application and hotkey scripts
6. Create desktop launcher

## Setup Autostart (Optional)

To make the app start automatically on login:

```bash
chmod +x setup_autostart.sh
./setup_autostart.sh
```

Then log out and log back in.

## Usage

### Starting the App

**After autostart setup:**
- Just log in, the app starts automatically

**Manual start:**
```bash
~/.local/share/voice-transcribe/run.sh
```

Or search for "Voice Transcribe" in your application menu.

### Recording

**Method 1: Using Tray Icon**
1. **Click the tray icon** - Icon turns green 🟢 (recording starts)
2. **Speak into your microphone**
3. **Click again to stop** - Icon turns yellow 🟡 (processing)
4. **Wait for processing** - Icon turns red 🔴 (done, text in clipboard)
5. **Paste anywhere** with Ctrl+V

**Method 2: Using Hotkeys (Must be enabled in Settings)**
1. **Press F9 or Alt+.** anywhere - Recording starts 🟢
2. **Speak into your microphone**
3. **Press F9 or Alt+. again** - Recording stops, processing begins 🟡
4. **Wait for processing** - Done, text in clipboard 🔴
5. **Paste anywhere** with Ctrl+V

### Enabling Hotkeys

Hotkeys are disabled by default. To enable:

1. Right-click the tray icon → **Settings**
2. Check ✅ **Enable Hotkeys**
3. (Optional) Click **Record Primary** or **Record Secondary** to change hotkeys
4. Click **Save**

Now you can use F9 or Alt+. from any application!

### Tips for Best Accuracy

- Use an external microphone (headset, USB mic, lapel mic)
- Speak clearly and at a moderate pace
- Reduce background noise
- Keep recordings under 5 minutes for faster processing

## Processing Times

Approximate times on i5 8th gen CPU:

| Audio Length | Processing Time |
|--------------|-----------------|
| 10 seconds   | 5-10 seconds    |
| 1 minute     | 20-30 seconds   |
| 5 minutes    | 1-2 minutes     |
| 10 minutes   | 2-3 minutes     |

## Uninstall

To completely remove the app:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

This removes:
- Application files
- Whisper.cpp
- Configuration and recordings
- Desktop launcher
- Autostart entry
- Hotkey registrations

Your repository folder is preserved.

## Project Structure

```
voice-transcribe/
├── voice_transcribe.py     # Main application
├── install.sh              # Installation script
├── setup_autostart.sh      # Autostart configuration
├── uninstall.sh            # Uninstaller
├── pyproject.toml          # UV project file
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Troubleshooting

### Tray icon doesn't appear

Install GNOME app indicator extension:

```bash
sudo apt install gnome-shell-extension-appindicator
gnome-extensions enable ubuntu-appindicators@ubuntu.com
```

Then log out and log back in.

### Hotkeys don't work

**Check 1:** Is "Enable Hotkeys" checked?
- Right-click tray icon → Settings
- Make sure ✅ Enable Hotkeys is checked

**Check 2:** Are you using GNOME?
- Hotkeys require GNOME desktop environment
- Check with: `echo $XDG_CURRENT_DESKTOP`
- If not GNOME, use tray icon click instead

**Check 3:** Key conflict?
- Try recording a different hotkey combination
- The app will warn you if a key is already in use

### "Whisper binary not found" error

Check settings (right-click tray icon → Settings) and verify path is:
```
/home/YOUR_USERNAME/whisper.cpp
```

### Poor transcription accuracy

- **Use an external microphone** - This is the #1 improvement
- Built-in laptop mics are omnidirectional and pick up too much noise
- Even a cheap ₹500 lapel mic will dramatically improve accuracy

### Permission errors with microphone

```bash
sudo usermod -a -G audio $USER
```

Then log out and log back in.

## Configuration

Settings are stored in: `~/.config/voice-transcribe/config.json`

Recordings (last 5) are kept in: `~/.config/voice-transcribe/recordings/`

Hotkey settings:
- `hotkey_enabled`: true/false
- `primary_hotkey`: Key combination (e.g., "F9")
- `secondary_hotkey`: Key combination (e.g., "Alt+.")

## Technology Stack

- **Python 3** - Application logic
- **PyQt5** - GUI and system tray
- **Whisper.cpp** - Speech recognition (base model)
- **UV** - Fast Python package manager
- **sounddevice** - Audio recording
- **D-Bus** - Hotkey communication
- **GNOME gsettings** - System hotkey registration

## How Hotkeys Work

1. App registers custom keybindings with GNOME Settings
2. GNOME listens for your hotkey globally (across all apps)
3. When pressed, GNOME executes a toggle script
4. Script sends D-Bus message to the app
5. App toggles recording (same as clicking tray icon)

This is a standard Linux approach using native APIs. No root required, minimal overhead.

## Credits

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- [OpenAI Whisper](https://github.com/openai/whisper) for the base model

---

**Made with ❤️ for offline voice transcription**