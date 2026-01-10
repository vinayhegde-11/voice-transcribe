# Voice Transcribe - Offline Speech-to-Text for Linux

🎤 A simple, offline voice transcription app for Ubuntu/Linux with system tray integration.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04-orange)

## Features

✅ **Completely Offline** - No internet required after setup  
✅ **System Tray Integration** - Runs quietly in the background  
✅ **Visual Feedback** - Color-coded status (Red/Green/Yellow)  
✅ **Auto Clipboard** - Transcribed text automatically copied  
✅ **No Notifications Spam** - Silent operation, just color changes  
✅ **Lightweight** - Works on CPU-only systems (i5 8th gen tested)  

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

### Recording

1. **Click the tray icon** - Icon turns green 🟢 (recording starts)
2. **Speak into your microphone**
3. **Click again to stop** - Icon turns yellow 🟡 (processing)
4. **Wait for processing** - Icon turns red 🔴 (done, text in clipboard)
5. **Paste anywhere** with Ctrl+V

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

## Project Structure

```
voice-transcribe/
├── voice_transcribe.py     # Main application
├── install.sh              # Installation script
├── setup_autostart.sh      # Autostart configuration
├── uninstall.sh            # Uninstaller
├── pyproject.toml          # UV project file
├── README.md               # This file
└── LICENSE                 # MIT License
```

## Troubleshooting

### Tray icon doesn't appear

Install GNOME app indicator extension:

```bash
sudo apt install gnome-shell-extension-appindicator
gnome-extensions enable ubuntu-appindicators@ubuntu.com
```

Then log out and log back in.

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

## Technology Stack

- **Python 3** - Application logic
- **PyQt5** - GUI and system tray
- **Whisper.cpp** - Speech recognition (base model)
- **UV** - Fast Python package manager
- **sounddevice** - Audio recording

## Credits

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- [OpenAI Whisper](https://github.com/openai/whisper) for the base model

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run from terminal to see error messages: `~/voice-transcribe/run.sh`
3. Open an issue on GitHub with error details

---

**Made with ❤️ for offline voice transcription**
