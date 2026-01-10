#!/bin/bash
# Setup autostart for Voice Transcribe App

set -e

echo "================================"
echo "Voice Transcribe - Autostart Setup"
echo "================================"
echo ""

INSTALL_DIR="$HOME/.local/share/voice-transcribe"
AUTOSTART_DIR="$HOME/.config/autostart"

# Check if installation exists
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
Hidden=false
EOF

chmod +x "$AUTOSTART_FILE"

# Test if the run script works
if [ ! -f "$INSTALL_DIR/run.sh" ]; then
    echo "Error: run.sh not found at $INSTALL_DIR/run.sh"
    exit 1
fi

chmod +x "$INSTALL_DIR/run.sh"

echo "✓ Autostart configured successfully!"
echo ""
echo "The app will now start automatically when you log in."
echo ""
echo "Testing autostart configuration:"
echo "  Autostart file: $AUTOSTART_FILE"
echo "  Run script: $INSTALL_DIR/run.sh"
echo ""
echo "To verify autostart is working:"
echo "  1. Log out and log back in"
echo "  2. Look for the red circle 🔴 in your system tray"
echo ""
echo "To disable autostart later:"
echo "  rm ~/.config/autostart/voice-transcribe.desktop"
echo ""
echo "To start the app now without rebooting:"
echo "  $INSTALL_DIR/run.sh &"
echo ""
echo "Note: The '&' runs it in background so you can close the terminal."
echo ""

# Offer to start it now
read -p "Start the app now in background? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    nohup "$INSTALL_DIR/run.sh" > /dev/null 2>&1 &
    echo "App started! Look for the red circle 🔴 in your tray."
fi
