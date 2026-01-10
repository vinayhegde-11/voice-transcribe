#!/bin/bash
# Uninstall script for Voice Transcribe App

set -e

echo "================================"
echo "Voice Transcribe - Uninstaller"
echo "================================"
echo ""
echo "This will remove:"
echo "  - Installed application files (~/.local/share/voice-transcribe)"
echo "  - Whisper.cpp (~whisper.cpp)"
echo "  - Configuration and recordings (~/.config/voice-transcribe)"
echo "  - Desktop launcher"
echo "  - Autostart entry"
echo ""
echo "NOTE: This will NOT remove the cloned repository folder."
echo "      You can safely delete that manually if needed."
echo ""
read -p "Are you sure you want to uninstall? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Uninstalling..."

# Stop running instance if any
echo "1. Stopping running instances..."
pkill -f voice_transcribe.py 2>/dev/null || true

# Remove installed application files (NOT the repo!)
echo "2. Removing installed application files..."
# Old location (if exists)
if [ -d "$HOME/voice-transcribe" ]; then
    # Check if it's the repo (has .git folder) or installed version
    if [ -d "$HOME/voice-transcribe/.git" ]; then
        echo "   Detected repository at ~/voice-transcribe, skipping..."
        echo "   (Only removing installed binaries and configs)"
    else
        rm -rf "$HOME/voice-transcribe"
        echo "   Removed ~/voice-transcribe"
    fi
fi

# Remove from .local/share if it exists there
if [ -d "$HOME/.local/share/voice-transcribe" ]; then
    rm -rf "$HOME/.local/share/voice-transcribe"
    echo "   Removed ~/.local/share/voice-transcribe"
fi

# Remove whisper.cpp
echo "3. Removing whisper.cpp..."
if [ -d "$HOME/whisper.cpp" ]; then
    rm -rf "$HOME/whisper.cpp"
    echo "   Removed ~/whisper.cpp"
fi

# Remove config and recordings
echo "4. Removing configuration and recordings..."
if [ -d "$HOME/.config/voice-transcribe" ]; then
    rm -rf "$HOME/.config/voice-transcribe"
    echo "   Removed ~/.config/voice-transcribe"
fi

# Remove desktop launcher
echo "5. Removing desktop launcher..."
if [ -f "$HOME/.local/share/applications/voice-transcribe.desktop" ]; then
    rm -f "$HOME/.local/share/applications/voice-transcribe.desktop"
    echo "   Removed desktop launcher"
fi

# Remove autostart entry
echo "6. Removing autostart entry..."
if [ -f "$HOME/.config/autostart/voice-transcribe.desktop" ]; then
    rm -f "$HOME/.config/autostart/voice-transcribe.desktop"
    echo "   Removed autostart entry"
fi

echo ""
echo "================================"
echo "Uninstall Complete!"
echo "================================"
echo ""
echo "All Voice Transcribe installed files have been removed."
echo ""
if [ -d "$HOME/voice-transcribe/.git" ]; then
    echo "Your repository folder (~/voice-transcribe) was preserved."
    echo "You can delete it manually if you want:"
    echo "  rm -rf ~/voice-transcribe"
    echo ""
fi
echo "Note: System packages (cmake, portaudio, etc.) were not removed"
echo "      as they may be used by other applications."
echo ""
echo "Note: UV package manager was not removed."
echo "      To remove UV: rm -rf ~/.cargo/bin/uv ~/.local/share/uv"
echo ""
