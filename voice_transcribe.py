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
                             QTextEdit, QVBoxLayout, QWidget, QPushButton, 
                             QHBoxLayout, QMessageBox, QDialog, QLabel,
                             QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QColor

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
            'hotkey_enabled': False,
            'hotkey': 'Ctrl+Shift+R',
            'sample_rate': 16000,
            'whisper_model': 'base',
            'whisper_path': str(Path.home() / 'whisper.cpp'),
            'max_recordings': 5
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = {**default_config, **json.load(f)}
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

class TranscriptionWindow(QWidget):
    def __init__(self, text):
        super().__init__()
        self.setWindowTitle('Transcription Result')
        self.setGeometry(300, 300, 600, 400)
        
        layout = QVBoxLayout()
        
        label = QLabel('Transcription (already copied to clipboard):')
        layout.addWidget(label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setFocus()
        layout.addWidget(self.text_edit)
        
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton('Copy Again')
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        QMessageBox.information(self, 'Copied', 'Text copied to clipboard!')

class SettingsDialog(QDialog):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle('Settings')
        self.setGeometry(400, 400, 400, 200)
        
        layout = QVBoxLayout()
        
        # Hotkey settings
        self.hotkey_checkbox = QCheckBox('Enable Hotkey')
        self.hotkey_checkbox.setChecked(config_manager.config['hotkey_enabled'])
        layout.addWidget(self.hotkey_checkbox)
        
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel('Hotkey:'))
        self.hotkey_input = QLineEdit(config_manager.config['hotkey'])
        self.hotkey_input.setEnabled(config_manager.config['hotkey_enabled'])
        hotkey_layout.addWidget(self.hotkey_input)
        layout.addLayout(hotkey_layout)
        
        self.hotkey_checkbox.stateChanged.connect(
            lambda: self.hotkey_input.setEnabled(self.hotkey_checkbox.isChecked())
        )
        
        # Whisper path
        whisper_layout = QHBoxLayout()
        whisper_layout.addWidget(QLabel('Whisper.cpp path:'))
        self.whisper_path = QLineEdit(config_manager.config['whisper_path'])
        whisper_layout.addWidget(self.whisper_path)
        layout.addLayout(whisper_layout)
        
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
    
    def save_settings(self):
        self.config_manager.config['hotkey_enabled'] = self.hotkey_checkbox.isChecked()
        self.config_manager.config['hotkey'] = self.hotkey_input.text()
        self.config_manager.config['whisper_path'] = self.whisper_path.text()
        self.config_manager.save_config()
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
        dialog = SettingsDialog(self.config)
        dialog.exec_()
    
    def quit_app(self):
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray_app = VoiceTranscribeApp()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
