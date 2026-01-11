# Voice Transcribe - Offline Speech-to-Text for Linux

🎤 A simple, offline voice transcription app for Ubuntu/Linux with system tray integration.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04-orange)

## Features

✅ **Completely Offline** - No internet required after setup  
✅ **System Tray Integration** - Runs quietly in the background  
✅ **Visual Feedback** - Color-coded status (Red/Green/Yellow)  
✅ **Multiple Hotkeys** - Support for multiple hotkey combinations  
✅ **Smart Conflict Detection** - Detects conflicts with system shortcuts  
✅ **Auto Clipboard** - Transcribed text automatically copied  
✅ **No Notifications Spam** - Silent operation, just color changes  
✅ **Lightweight** - Works on CPU-only systems (i5 8th gen tested)  
✅ **Robust Error Handling** - Clear error messages and auto-recovery  
✅ **Config Validation** - Auto-fixes corrupted settings  

## Visual Status Indicators

🔴 **Red Circle** - Ready to record (click to start)  
🟢 **Green Circle** - Recording in progress (click to stop)  
🟡 **Yellow Circle** - Processing transcription  
🔴 **Red Circle** - Done! Text in clipboard, ready for next recording  

## Requirements

- Ubuntu 24.04 (or similar Debian-based distro)
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
5. Set up the application
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
~/voice-transcribe/run.sh
```

Or search for "Voice Transcribe" in your application menu.

### Hotkey Setup

1. Right-click the tray icon → **Settings**
2. Check **"Enable Hotkeys"**
3. Click **"Add Hotkey"**
4. Press your desired key combination (e.g., `F9` or `Alt+.`)
5. Repeat to add more hotkeys (useful for different keyboards)
6. Click **"Save"**

**Note:** The app detects conflicts with system shortcuts and warns you.

### Recording

**Using Hotkey:**
1. Press your hotkey (e.g., `F9`) → Icon turns green 🟢 (recording starts)
2. Speak into your microphone
3. Press hotkey again → Icon turns yellow 🟡 (processing)
4. Wait for processing → Icon turns red 🔴 (done, text in clipboard)
5. Paste anywhere with `Ctrl+V`

**Using Tray Icon:**
1. Click the tray icon (same behavior as hotkey)

### Tips for Best Accuracy

- **Use an external microphone** (headset, USB mic, lapel mic)
- Built-in laptop mics pick up too much background noise
- Speak clearly and at a moderate pace
- Reduce background noise
- Keep recordings under 5 minutes for faster processing
- Even a cheap ₹500 lapel mic dramatically improves accuracy

## Hotkey Recommendations

The app supports multiple hotkeys simultaneously. Useful for different keyboards:

**Recommended combinations:**
- `F9` - Single key, very fast (good for external keyboards)
- `Alt+.` - Comfortable right-hand (works on all keyboards)
- `Alt+,` - Alternative to Alt+.
- `Alt+;` - Another comfortable option

**Avoid system shortcuts like:**
- `Ctrl+Alt+T` (terminal)
- `Alt+F4` (close window)
- `Super+L` (lock screen)

The app will detect conflicts and warn you.

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

## Project Structure

```
voice-transcribe/
├── voice_transcribe.py     # Main application
├── install.sh              # Installation script
├── setup_autostart.sh      # Autostart configuration
├── uninstall.sh            # Uninstaller
├── pyproject.toml          # UV project file
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

### Hotkeys not working

1. Make sure you're on GNOME desktop environment
2. Check Settings → Enable Hotkeys is checked
3. Try removing and re-adding the hotkey
4. Check terminal for errors: `~/.local/share/voice-transcribe/run.sh`

### "Whisper binary not found" error

The app will show the exact path it's looking for. Verify:
```bash
ls ~/whisper.cpp/build/bin/whisper-cli
```

If missing, rebuild whisper:
```bash
cd ~/whisper.cpp
make clean
make
```

### "Model not found" error

Download the model:
```bash
cd ~/whisper.cpp
bash ./models/download-ggml-model.sh base
```

### Poor transcription accuracy

**#1 Solution: Use an external microphone!**
- Built-in laptop mics are poor quality
- Even a ₹500 lapel mic makes huge difference
- USB headsets work great

**Other tips:**
- Speak closer to the microphone
- Check microphone volume in system settings
- Reduce background noise (close windows, turn off fans)

### "Could not access microphone" error

Check permissions:
```bash
sudo usermod -a -G audio $USER
```

Then log out and log back in.

Verify microphone works:
```bash
arecord -d 5 test.wav
aplay test.wav
```

### Config file corrupted

The app auto-validates and fixes corrupted configs. If issues persist:
```bash
rm ~/.config/voice-transcribe/config.json
# Restart the app - it will create a fresh config
```

## Configuration

Settings are stored in: `~/.config/voice-transcribe/config.json`

Recordings (last 5) are kept in: `~/.config/voice-transcribe/recordings/`

### Config File Format
```json
{
  "hotkeys_enabled": false,
  "hotkeys": ["F9", "Alt+."],
  "sample_rate": 16000,
  "whisper_model": "base",
  "whisper_path": "/home/username/whisper.cpp",
  "max_recordings": 5
}
```

**Valid values:**
- `sample_rate`: 8000-48000 (default: 16000)
- `whisper_model`: tiny, base, small, medium, large
- `max_recordings`: 1-100 (default: 5)

The app automatically validates and fixes invalid values.

## Technology Stack

- **Python 3** - Application logic
- **PyQt5** - GUI and system tray
- **Whisper.cpp** - Speech recognition (base model)
- **UV** - Fast Python package manager
- **sounddevice** - Audio recording
- **GNOME gsettings** - System hotkey integration

## Recent Improvements (v1.0.0)

- ✅ Multiple hotkey support
- ✅ Real-time conflict detection with system shortcuts
- ✅ Thread pool for controlled transcription processing
- ✅ Config validation and auto-repair
- ✅ Better error messages with troubleshooting hints
- ✅ Microphone permission handling
- ✅ Empty recording detection
- ✅ Icon helper method (DRY code)
- ✅ Removed CPU-intensive polling (event-driven only)

## Credits

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- [OpenAI Whisper](https://github.com/openai/whisper) for the base model

---

**Made with ❤️ for offline voice transcription**