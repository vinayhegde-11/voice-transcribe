#!/usr/bin/env python3
"""
Voice Transcription Tray Application
Offline speech-to-text using Whisper
"""

import sys
import os
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import sounddevice as sd
import scipy.io.wavfile as wav
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction, 
                             QVBoxLayout, QWidget, QPushButton, 
                             QHBoxLayout, QMessageBox, QDialog, QLabel,
                             QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QKeySequence

class TranscriptionSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'voice-transcribe'
        self.config_file = self.config_dir / 'config.json'
        self.recordings_dir = self.config_dir / 'recordings'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_dir.mkdir(exist_ok=True)
        self.load_config()
    
    def load_config(self):
        default_config = {
            'hotkeys_enabled': False,
            'hotkeys': ['F9', 'Alt+.'],
            'sample_rate': 16000,
            'whisper_model': 'base',
            'whisper_path': str(Path.home() / 'whisper.cpp'),
            'max_recordings': 5
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                loaded = json.load(f)
                # Migrate old config format
                if 'hotkey' in loaded:
                    loaded['hotkeys'] = [loaded.pop('hotkey')]
                if 'hotkey_enabled' in loaded:
                    loaded['hotkeys_enabled'] = loaded.pop('hotkey_enabled')
                self.config = {**default_config, **loaded}
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def cleanup_old_recordings(self):
        recordings = sorted(self.recordings_dir.glob('*.wav'), key=os.path.getmtime)
        while len(recordings) > self.config['max_recordings']:
            oldest = recordings.pop(0)
            oldest.unlink()

class HotkeyRecorder(QDialog):
    """Dialog for recording a new hotkey combination"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Record Hotkey')
        self.setModal(True)
        self.recorded_keys = []
        self.recording = False
        
        layout = QVBoxLayout()
        
        self.label = QLabel('Press ESC to cancel or press your desired key combination...')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(self.label)
        
        self.keys_label = QLabel('')
        self.keys_label.setAlignment(Qt.AlignCenter)
        self.keys_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; padding: 10px;")
        layout.addWidget(self.keys_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(400)
        self.recording = True
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        
        if self.recording:
            # Get modifiers
            modifiers = []
            if event.modifiers() & Qt.ControlModifier:
                modifiers.append('Ctrl')
            if event.modifiers() & Qt.AltModifier:
                modifiers.append('Alt')
            if event.modifiers() & Qt.ShiftModifier:
                modifiers.append('Shift')
            if event.modifiers() & Qt.MetaModifier:
                modifiers.append('Super')
            
            # Get the actual key
            key = event.key()
            key_text = QKeySequence(key).toString()
            
            # Ignore if it's just a modifier key
            if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
                return
            
            # Build the combination
            if modifiers:
                combination = '+'.join(modifiers + [key_text])
            else:
                combination = key_text
            
            self.keys_label.setText(combination)
            self.recorded_keys = combination
            self.recording = False
            
            # Auto-close after showing for 1 second
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self.accept)

class SettingsDialog(QDialog):
    def __init__(self, config_manager, app, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.app = app
        self.setWindowTitle('Settings')
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Hotkey settings group
        hotkey_group = QGroupBox('Hotkey Settings')
        hotkey_layout = QVBoxLayout()
        
        self.hotkey_checkbox = QCheckBox('Enable Hotkeys')
        self.hotkey_checkbox.setChecked(config_manager.config['hotkeys_enabled'])
        hotkey_layout.addWidget(self.hotkey_checkbox)
        
        # Display current hotkeys
        self.hotkeys_display = QLabel()
        self.hotkeys_display.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        hotkey_layout.addWidget(self.hotkeys_display)
        
        # Buttons for managing hotkeys
        hotkey_buttons = QHBoxLayout()
        
        self.add_hotkey_btn = QPushButton('Add Hotkey')
        self.add_hotkey_btn.clicked.connect(self.add_hotkey)
        hotkey_buttons.addWidget(self.add_hotkey_btn)
        
        self.remove_hotkey_btn = QPushButton('Remove Last Hotkey')
        self.remove_hotkey_btn.clicked.connect(self.remove_hotkey)
        hotkey_buttons.addWidget(self.remove_hotkey_btn)
        
        # Now update the display after all widgets are created
        self.update_hotkeys_display()
        
        hotkey_layout.addLayout(hotkey_buttons)
        
        # Warning label
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: #f44336; padding: 5px;")
        self.warning_label.setWordWrap(True)
        hotkey_layout.addWidget(self.warning_label)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # Whisper path
        whisper_layout = QHBoxLayout()
        whisper_layout.addWidget(QLabel('Whisper.cpp path:'))
        self.whisper_path = QLabel(config_manager.config['whisper_path'])
        self.whisper_path.setStyleSheet("padding: 5px; background: #f0f0f0; border-radius: 3px;")
        whisper_layout.addWidget(self.whisper_path)
        layout.addLayout(whisper_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def update_hotkeys_display(self):
        hotkeys = self.config_manager.config['hotkeys']
        if hotkeys:
            display_text = 'Current Hotkeys:\n' + '\n'.join(f'  • {hk}' for hk in hotkeys)
        else:
            display_text = 'No hotkeys configured'
        self.hotkeys_display.setText(display_text)
        self.remove_hotkey_btn.setEnabled(len(hotkeys) > 0)
    
    def add_hotkey(self):
        recorder = HotkeyRecorder(self)
        if recorder.exec_() == QDialog.Accepted:
            new_hotkey = recorder.recorded_keys
            
            if not new_hotkey:
                return
            
            # Check if already exists
            if new_hotkey in self.config_manager.config['hotkeys']:
                QMessageBox.warning(self, 'Duplicate', 
                                  f'Hotkey "{new_hotkey}" is already configured.')
                return
            
            # Check for system conflicts
            if self.check_system_conflict(new_hotkey):
                reply = QMessageBox.question(self, 'Conflict Detected',
                    f'⚠️ The key combination "{new_hotkey}" may be in use by the system.\n\n'
                    'Do you want to use it anyway?',
                    QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.No:
                    return
            
            # Add to list
            self.config_manager.config['hotkeys'].append(new_hotkey)
            self.update_hotkeys_display()
    
    def remove_hotkey(self):
        if self.config_manager.config['hotkeys']:
            removed = self.config_manager.config['hotkeys'].pop()
            self.update_hotkeys_display()
            QMessageBox.information(self, 'Removed', f'Removed hotkey: {removed}')
    
    def check_system_conflict(self, hotkey):
        """Check if hotkey might conflict with system shortcuts"""
        # Common system shortcuts that might conflict
        system_shortcuts = [
            'Ctrl+Alt+T', 'Ctrl+Alt+L', 'Super+L', 'Alt+F1', 'Alt+F2',
            'Alt+F4', 'Ctrl+Alt+D', 'Super+D', 'Alt+Tab', 'Super+Tab'
        ]
        return hotkey in system_shortcuts
    
    def save_settings(self):
        old_enabled = self.config_manager.config['hotkeys_enabled']
        old_hotkeys = self.config_manager.config['hotkeys'].copy()
        
        self.config_manager.config['hotkeys_enabled'] = self.hotkey_checkbox.isChecked()
        self.config_manager.save_config()
        
        # Try to register/unregister hotkeys
        if self.config_manager.config['hotkeys_enabled']:
            success = self.app.register_hotkeys()
            if not success:
                QMessageBox.critical(self, 'Hotkey Registration Failed',
                    '❌ Failed to register hotkeys with the system.\n\n'
                    'This feature requires GNOME desktop environment.\n'
                    'Hotkey feature will be disabled.')
                self.config_manager.config['hotkeys_enabled'] = False
                self.config_manager.save_config()
        else:
            self.app.unregister_hotkeys()
        
        QMessageBox.information(self, 'Saved', 'Settings saved successfully!')
        self.close()

class VoiceTranscribeApp(QSystemTrayIcon):
    def __init__(self):
        # Create a circular colored icon - RED (idle/ready)
        from PyQt5.QtGui import QPainter
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#F44336'))  # Red - ready to record
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        painter.end()
        icon = QIcon(pixmap)
        
        super().__init__(icon)
        
        self.config = ConfigManager()
        self.recording = False
        self.audio_data = []
        self.stream = None
        self.signals = TranscriptionSignals()
        self.signals.finished.connect(self.on_transcription_finished)
        self.signals.error.connect(self.on_transcription_error)
        self.hotkey_ids = []
        
        # Setup IPC for hotkey communication
        self.ipc_file = self.config.config_dir / 'hotkey_trigger'
        self.setup_ipc_watcher()
        
        # Create menu
        self.menu = QMenu()
        
        self.record_action = QAction('Start Recording', self.menu)
        self.record_action.triggered.connect(self.toggle_recording)
        self.menu.addAction(self.record_action)
        
        self.menu.addSeparator()
        
        settings_action = QAction('Settings', self.menu)
        settings_action.triggered.connect(self.show_settings)
        self.menu.addAction(settings_action)
        
        quit_action = QAction('Quit', self.menu)
        quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_tray_activated)
        
        self.show()
        
        # Register hotkeys if enabled
        if self.config.config['hotkeys_enabled']:
            self.register_hotkeys()
    
    def setup_ipc_watcher(self):
        """Setup file watcher for IPC communication"""
        from PyQt5.QtCore import QTimer, QFileSystemWatcher
        
        # Ensure IPC file doesn't exist at start
        if self.ipc_file.exists():
            self.ipc_file.unlink()
        
        # Watch the directory for file changes
        self.file_watcher = QFileSystemWatcher([str(self.config.config_dir)])
        self.file_watcher.directoryChanged.connect(self.check_ipc_trigger)
        
        # Also poll periodically as backup
        self.ipc_timer = QTimer()
        self.ipc_timer.timeout.connect(self.check_ipc_trigger)
        self.ipc_timer.start(500)  # Check every 500ms
    
    def check_ipc_trigger(self):
        """Check if hotkey was triggered via IPC"""
        if self.ipc_file.exists():
            try:
                # Read and delete the trigger file
                self.ipc_file.unlink()
                # Toggle recording
                self.toggle_recording()
            except:
                pass
    
    def register_hotkeys(self):
        """Register hotkeys with GNOME"""
        try:
            # Check if we're on GNOME
            desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
            if 'gnome' not in desktop:
                return False
            
            # Create toggle script if it doesn't exist
            toggle_script = self.config.config_dir / 'toggle.sh'
            with open(toggle_script, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('# Toggle voice transcribe recording\n')
                f.write(f'touch {self.ipc_file}\n')
            toggle_script.chmod(0o755)
            
            # Register each hotkey
            hotkeys = self.config.config['hotkeys']
            for i, hotkey in enumerate(hotkeys):
                binding_path = f'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/voice-transcribe-{i}/'
                
                # Set the keybinding
                subprocess.run([
                    'gsettings', 'set',
                    f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{binding_path}',
                    'name', f'Voice Transcribe {i+1}'
                ], check=True)
                
                subprocess.run([
                    'gsettings', 'set',
                    f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{binding_path}',
                    'command', str(toggle_script)
                ], check=True)
                
                # Convert our format to GNOME format
                gnome_binding = self.convert_to_gnome_format(hotkey)
                subprocess.run([
                    'gsettings', 'set',
                    f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{binding_path}',
                    'binding', gnome_binding
                ], check=True)
                
                self.hotkey_ids.append(binding_path)
            
            # Add to the list of custom keybindings
            existing = subprocess.run([
                'gsettings', 'get',
                'org.gnome.settings-daemon.plugins.media-keys',
                'custom-keybindings'
            ], capture_output=True, text=True).stdout.strip()
            
            # Parse existing list
            if existing == '@as []':
                new_list = [f"'{binding_path}'" for binding_path in self.hotkey_ids]
            else:
                # Remove brackets and split
                existing = existing.strip('[]').split(',')
                existing = [e.strip() for e in existing if e.strip()]
                # Add new paths
                for binding_path in self.hotkey_ids:
                    path_str = f"'{binding_path}'"
                    if path_str not in existing:
                        existing.append(path_str)
                new_list = existing
            
            new_list_str = '[' + ', '.join(new_list) + ']'
            subprocess.run([
                'gsettings', 'set',
                'org.gnome.settings-daemon.plugins.media-keys',
                'custom-keybindings', new_list_str
            ], check=True)
            
            return True
            
        except Exception as e:
            print(f"Failed to register hotkeys: {e}")
            return False
    
    def convert_to_gnome_format(self, hotkey):
        """Convert our hotkey format to GNOME format"""
        # Our format: Ctrl+Shift+R or Alt+. or F9
        # GNOME format: <Primary><Shift>r or <Alt>period or F9
        
        mapping = {
            'Ctrl': '<Primary>',
            'Alt': '<Alt>',
            'Shift': '<Shift>',
            'Super': '<Super>',
            '.': 'period',
            ',': 'comma',
            ';': 'semicolon',
            "'": 'apostrophe',
            '`': 'grave'
        }
        
        parts = hotkey.split('+')
        result = ''
        
        for part in parts[:-1]:  # All except last are modifiers
            result += mapping.get(part, f'<{part}>')
        
        # Last part is the key
        key = parts[-1]
        result += mapping.get(key, key.lower())
        
        return result
    
    def unregister_hotkeys(self):
        """Unregister hotkeys from GNOME"""
        try:
            if not self.hotkey_ids:
                return
            
            # Remove from custom keybindings list
            existing = subprocess.run([
                'gsettings', 'get',
                'org.gnome.settings-daemon.plugins.media-keys',
                'custom-keybindings'
            ], capture_output=True, text=True).stdout.strip()
            
            if existing != '@as []':
                existing = existing.strip('[]').split(',')
                existing = [e.strip() for e in existing if e.strip()]
                # Remove our paths
                for binding_path in self.hotkey_ids:
                    path_str = f"'{binding_path}'"
                    if path_str in existing:
                        existing.remove(path_str)
                
                if existing:
                    new_list_str = '[' + ', '.join(existing) + ']'
                else:
                    new_list_str = '@as []'
                
                subprocess.run([
                    'gsettings', 'set',
                    'org.gnome.settings-daemon.plugins.media-keys',
                    'custom-keybindings', new_list_str
                ], check=True)
            
            self.hotkey_ids = []
            
        except Exception as e:
            print(f"Failed to unregister hotkeys: {e}")
    
    def show_notification(self, title, message, urgency=1):
        """Show native Ubuntu desktop notification"""
        try:
            # Try using notify-send command (more reliable)
            subprocess.run([
                'notify-send',
                '-a', 'Voice Transcribe',
                '-i', 'audio-input-microphone',
                '-t', '5000',
                title,
                message
            ], check=False)
        except:
            # Fallback to tray notification
            self.showMessage(title, message, QSystemTrayIcon.Information, 5000)
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_recording()
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        from PyQt5.QtGui import QPainter
        
        self.recording = True
        self.audio_data = []
        
        # Change icon color to green circle (recording)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#4CAF50'))  # Green - recording
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        painter.end()
        self.setIcon(QIcon(pixmap))
        
        self.record_action.setText('Stop Recording')
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(status)
            self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.config.config['sample_rate'],
            channels=1,
            callback=audio_callback
        )
        self.stream.start()
    
    def stop_recording(self):
        from PyQt5.QtGui import QPainter
        
        self.recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Change icon to yellow circle (processing)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#FFC107'))  # Yellow - processing
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        painter.end()
        self.setIcon(QIcon(pixmap))
        
        self.record_action.setText('Start Recording')
        
        # Save audio and start transcription in background
        threading.Thread(target=self.process_audio, daemon=True).start()
    
    def process_audio(self):
        try:
            import numpy as np
            
            # Combine audio data
            audio = np.concatenate(self.audio_data, axis=0)
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_file = self.config.recordings_dir / f'recording_{timestamp}.wav'
            
            wav.write(str(audio_file), self.config.config['sample_rate'], audio)
            
            # Cleanup old recordings
            self.config.cleanup_old_recordings()
            
            # Run whisper
            whisper_path = Path(self.config.config['whisper_path'])
            # Try different binary names and locations
            main_binary = whisper_path / 'build' / 'bin' / 'whisper-cli'
            if not main_binary.exists():
                main_binary = whisper_path / 'build' / 'bin' / 'main'
            if not main_binary.exists():
                main_binary = whisper_path / 'main'
            model_path = whisper_path / 'models' / f'ggml-{self.config.config["whisper_model"]}.bin'
            
            if not main_binary.exists():
                self.signals.error.emit(f'Whisper binary not found at {main_binary}')
                return
            
            if not model_path.exists():
                self.signals.error.emit(f'Model not found at {model_path}')
                return
            
            result = subprocess.run(
                [str(main_binary), '-m', str(model_path), '-f', str(audio_file), '-nt'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract text from output
                text = result.stdout.strip()
                # Remove timestamp prefixes that whisper adds
                lines = [line.split(']', 1)[-1].strip() if ']' in line else line 
                        for line in text.split('\n')]
                text = ' '.join(lines).strip()
                
                if text:
                    self.signals.finished.emit(text)
                else:
                    self.signals.error.emit('No speech detected')
            else:
                self.signals.error.emit(f'Transcription failed: {result.stderr}')
                
        except Exception as e:
            self.signals.error.emit(f'Error: {str(e)}')
    
    def on_transcription_finished(self, text):
        from PyQt5.QtGui import QPainter
        
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # Change icon back to red (ready)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#F44336'))  # Red - ready
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        painter.end()
        self.setIcon(QIcon(pixmap))
    
    def on_transcription_error(self, error_msg):
        from PyQt5.QtGui import QPainter
        
        # Show error notification (only for errors)
        self.show_notification('Error', error_msg)
        
        # Change icon back to red (ready)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#F44336'))  # Red - ready
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        painter.end()
        self.setIcon(QIcon(pixmap))
    
    def show_settings(self):
        dialog = SettingsDialog(self.config, self)
        dialog.exec_()
    
    def quit_app(self):
        # Unregister hotkeys on quit
        if self.config.config['hotkeys_enabled']:
            self.unregister_hotkeys()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray_app = VoiceTranscribeApp()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()