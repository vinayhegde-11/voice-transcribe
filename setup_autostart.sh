#!/bin/bash
# Setup autostart for Voice Transcribe App

set -e

echo "================================"
echo "Voice Transcribe - Autostart Setup"
echo "================================"
echo ""

INSTALL_DIR="$HOME/.local/share/voice-transcribe"
AUTOSTART_DIR="$HOME/.config/autostart"

# Check if app is installed
if [ ! -f "$INSTALL_DIR/voice_transcribe.py" ]; then
    echo "Error: Voice Transcribe is not installed."
    echo "Please run install.sh first."
    exit 1
fi

# Create autostart directory if it doesn't exist
mkdir -p "$AUTOSTART_DIR"

# Create autostart desktop file
AUTOSTART_FILE="$AUTOSTART_DIR/voice-transcribe.desktop"

cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Voice Transcribe
Comment=Offline voice transcription (autostart)
Exec=$INSTALL_DIR/run.sh
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Audio;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$AUTOSTART_FILE"

echo "✓ Autostart configured!"
echo ""
echo "The app will now start automatically when you log in."
echo ""
echo "To manage autostart:"
echo "1. Open 'Startup Applications' from your application menu"
echo "2. Look for 'Voice Transcribe'"
echo "3. Toggle it on/off as needed"
echo ""
echo "To start it now without rebooting:"
echo "$INSTALL_DIR/run.sh &"
echo ""
echo "The '&' at the end runs it in the background, so you can close the terminal."
echo ""
echo "HOTKEY SETUP:"
echo "-------------"
echo "Hotkeys are disabled by default. To enable:"
echo "1. Start the app (it will run in system tray)"
echo "2. Right-click the tray icon → Settings"
echo "3. Check 'Enable Hotkeys'"
echo "4. Adjust hotkeys if needed (default: F9 and Alt+.)"
echo "5. Click Save"
echo ""
echo "The hotkeys will work globally, even when other apps are in focus!"
echo ""