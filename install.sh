#!/bin/bash
# Installation script for Voice Transcribe App (using UV)

set -e

echo "================================"
echo "Voice Transcribe App - Installer"
echo "================================"
echo ""

# Check if running on Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo "Warning: This script is designed for Ubuntu/Debian systems"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install system dependencies (including cmake!)
echo "Step 1: Installing system dependencies..."
sudo apt update
sudo apt install -y git build-essential cmake portaudio19-dev curl libnotify-bin

# Install UV if not already installed
echo ""
echo "Step 2: Installing UV..."
if ! command -v uv &> /dev/null; then
    echo "UV not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    source "$HOME/.cargo/env" 2>/dev/null || true
else
    echo "UV already installed, skipping..."
fi

# Verify UV installation
if ! command -v uv &> /dev/null; then
    echo "Error: UV installation failed. Please install manually:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if voice_transcribe.py exists in script directory
if [ ! -f "$SCRIPT_DIR/voice_transcribe.py" ]; then
    echo ""
    echo "Error: voice_transcribe.py not found in $SCRIPT_DIR"
    echo "Please ensure all files from the repository are present."
    exit 1
fi

# Create project directory
echo ""
echo "Step 3: Setting up project directory..."
INSTALL_DIR="$HOME/.local/share/voice-transcribe"
mkdir -p "$INSTALL_DIR"

# Copy application files to install directory
echo "Copying application files..."
cp "$SCRIPT_DIR/voice_transcribe.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true

cd "$INSTALL_DIR"

# Initialize UV project and install dependencies
echo ""
echo "Step 4: Installing Python dependencies with UV..."
if [ ! -f "pyproject.toml" ]; then
    # Create pyproject.toml if it doesn't exist
    cat > pyproject.toml << 'EOF'
[project]
name = "voice-transcribe"
version = "1.0.0"
description = "Offline voice transcription app for Linux"
requires-python = ">=3.8"
dependencies = [
    "PyQt5>=5.15.0",
    "sounddevice>=0.4.6",
    "scipy>=1.10.0",
    "numpy>=1.24.0",
]
EOF
fi

uv sync

# Clone and build whisper.cpp
echo ""
echo "Step 5: Downloading and building whisper.cpp..."
WHISPER_DIR="$HOME/whisper.cpp"

if [ -d "$WHISPER_DIR" ]; then
    echo "whisper.cpp directory already exists. Updating..."
    cd "$WHISPER_DIR"
    git pull
else
    git clone https://github.com/ggerganov/whisper.cpp.git "$WHISPER_DIR"
    cd "$WHISPER_DIR"
fi

# Build whisper.cpp
echo "Building whisper.cpp (this may take a few minutes)..."
make clean 2>/dev/null || true
make

# Verify build
if [ ! -f "$WHISPER_DIR/build/bin/whisper-cli" ] && [ ! -f "$WHISPER_DIR/build/bin/main" ]; then
    echo "Error: Whisper build failed. Binary not found."
    exit 1
fi

# Download base model
echo ""
echo "Step 6: Downloading Whisper base model (~150MB)..."
cd "$WHISPER_DIR"

# Check if model already exists
if [ -f "$WHISPER_DIR/models/ggml-base.bin" ]; then
    echo "Model already exists, skipping download..."
else
    # Try download script first
    if [ -f "./models/download-ggml-model.sh" ]; then
        bash ./models/download-ggml-model.sh base
    else
        # Fallback to direct download
        mkdir -p models
        cd models
        echo "Downloading model directly..."
        wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
        cd ..
    fi
fi

# Verify model download
if [ ! -f "$WHISPER_DIR/models/ggml-base.bin" ]; then
    echo "Error: Model download failed!"
    echo "Please manually download from:"
    echo "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
    echo "And save to: $WHISPER_DIR/models/ggml-base.bin"
    exit 1
fi

echo "Model downloaded successfully ($(du -h $WHISPER_DIR/models/ggml-base.bin | cut -f1))"

# Setup the application
echo ""
echo "Step 7: Finalizing installation..."
cd "$INSTALL_DIR"

# Make script executable
chmod +x voice_transcribe.py

# Create toggle script for hotkeys
echo "Creating hotkey toggle script..."
cat > "$INSTALL_DIR/toggle.sh" << 'EOF'
#!/bin/bash
# Toggle script for Voice Transcribe hotkeys
# Sends D-Bus signal to running app

qdbus com.voicetranscribe.app / Toggle 2>/dev/null || \
dbus-send --session --type=method_call \
  --dest=com.voicetranscribe.app \
  / \
  com.voicetranscribe.app.Toggle 2>/dev/null
EOF

chmod +x "$INSTALL_DIR/toggle.sh"

# Create config directory and default config
mkdir -p "$HOME/.config/voice-transcribe"
if [ ! -f "$HOME/.config/voice-transcribe/config.json" ]; then
    cat > "$HOME/.config/voice-transcribe/config.json" << EOF
{
  "hotkey_enabled": false,
  "hotkey": "Ctrl+Shift+R",
  "sample_rate": 16000,
  "whisper_model": "base",
  "whisper_path": "$HOME/whisper.cpp",
  "max_recordings": 5
}
EOF
fi

# Create desktop launcher
echo ""
echo "Step 8: Creating desktop launcher..."
DESKTOP_FILE="$HOME/.local/share/applications/voice-transcribe.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Voice Transcribe
Comment=Offline voice transcription
Exec=$INSTALL_DIR/run.sh
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Audio;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"

# Create launcher script for UV
cat > "$INSTALL_DIR/run.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
uv run voice_transcribe.py
EOF

chmod +x "$INSTALL_DIR/run.sh"

echo ""
echo "================================"
echo "Installation Complete!"
echo "================================"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Whisper.cpp directory: $WHISPER_DIR"
echo "Model location: $WHISPER_DIR/models/ggml-base.bin"
echo ""
echo "To run the application:"
echo "1. Using launcher: Search for 'Voice Transcribe' in your application menu"
echo "2. Using terminal: $INSTALL_DIR/run.sh"
echo "   Or: cd $INSTALL_DIR && uv run voice_transcribe.py"
echo ""
echo "Status indicators:"
echo "  🔴 Red circle   - Ready to record"
echo "  🟢 Green circle - Recording"
echo "  🟡 Yellow circle - Processing"
echo "  🔴 Red circle   - Done (text in clipboard)"
echo ""
echo "Configuration: ~/.config/voice-transcribe/config.json"
echo "Recordings (last 5): ~/.config/voice-transcribe/recordings/"
echo ""
echo "To make it start automatically on login, run:"
echo "  ./setup_autostart.sh"
echo ""
echo "Note: If the tray icon doesn't appear, you may need to enable"
echo "the app indicator extension. See README.md for details."
echo ""