
import os, sys
import csv
import google.generativeai
import google.generativeai as genai
from PIL import Image
import base64
import io
import pandas as pd
import pandas
import json, re, getpass

from PyQt6 import QtWidgets, QtCore, QtGui, uic
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from appdirs import user_config_dir

def get_config_file():
    # Get the current username
    username = getpass.getuser()

    # Define your application name and author/company name
    app_name = "gemeni-receipts"
    app_author = "gemini-receipts"  # Optional, not needed for Linux

    # Get the user-specific configuration directory
    config_dir = user_config_dir(app_name, app_author)

    # Create the configuration directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    # Define the path for your configuration file
    config_file = os.path.join(config_dir, f"{username}_settings.conf")
    return config_file

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str, str)

    def __init__(self, main_app, model,output_csv, input_folder):
        super().__init__()
        self.main_app = main_app
        self.progress.emit('Initializing Gemini model...\n', 'black')
        self.model = model
        self.input_folder = input_folder
        self.output_csv = output_csv

        # Supported image formats
        self.valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')

    def run(self):
        self.main_app.stopped = False
        self.progress.emit("Running...\n", 'black')
        rows = []

        # Loop through images
        for filename in os.listdir(self.input_folder):

            if self.main_app.stopped:
                self.main_app.run_button.setEnabled(True)
                self.main_app.run_button.setText('PROCESS')
                self.main_app.update_log('Process Stopped', 'red')
                self.finished.emit()
                break

            if filename.lower().endswith(self.valid_extensions):
                filepath = os.path.join(self.input_folder, filename)
                self.progress.emit(f"Processing {filename}...", 'black')

                # Open image with PIL
                image = Image.open(filepath)

                # Send image + prompt to Gemini
                prompt = """
        You are an assistant extracting receipt data from images.
        There may be more than one receipt in this image.

        Vendor | Location | Category | Subtotal | Taxes | Tip | Total | Date

        Return a JSON list of receipts. Each receipt should have:
        - vendor (string)
        - location (string)
        - category (string)
        - subtotal (string or float)
        - taxes (string or float)
        - tip (string or float)
        - total (string or float)
        - date (ISO format preferred)
        Do not include any other text or explanation. Only JSON.

        Example output:
        [
        {"vendor": "Starbucks", "location" : "Montreal", "category": "restaurant", "subtotal" : "50.95", "taxes" : "9.76", "tip" : "3.55", "total": "64.26", "date": "2024-02-13"},
        {"vendor": "Target", "location" : "Toronto", "category": "clothing", "subtotal" : "70.44", "taxes" : "12.28", "tip" : "", "total": "86.72", "date": "2024-12-30"},
        ]
        """
                try:
                    response = self.model.generate_content(
                        [prompt, image],
                        generation_config={"temperature": 0.2}
                    )
                    json_data = response.text.strip()

                    self.progress.emit(f"Model response: {json_data}\n\n", "gray")           
                    match = re.search(r'\[\s*{.*?}\s*]', json_data, re.DOTALL)
                    if match:
                        clean_json = match.group(0)
                        receipts = json.loads(clean_json)
                    else:
                        raise ValueError("No valid JSON array found in the model response.")
                        self.progress.emit(f"No valid JSON array found in the model response.", "red")
                    
                    for r in receipts:
                        rows.append({
                            "vendor": r.get("vendor", ""),
                            "location": r.get("location", ""),
                            "category": r.get("category", ""),
                            "subtotal": r.get("subtotal", ""),
                            "taxes": r.get("taxes", ""),
                            "tip": r.get("tip", ""),
                            "total": r.get("total", ""),
                            "date": r.get("date", ""),
                            "image": filename
                        })
                except Exception as e:
                    print(f"Error processing {filename}: {e}", "black")
                    self.progress.emit(f"Error processing {filename}: {e}", "red")

        # Save to CSV
        self.progress.emit("Saving to CSV...", 'black')
        df = pd.DataFrame(rows)
        df.to_csv(self.output_csv, index=False)
        print(f"\n✅ Done! CSV saved as: {self.output_csv}")
        self.progress.emit(f"\n✅ Done! CSV saved as: {self.output_csv}", "green")
        self.main_app.run_button.setEnabled(True)
        self.main_app.run_button.setText('PROCESS')
        self.finished.emit()


class gemini_receipt(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        parent_folder = os.path.dirname(__file__)
        uic.loadUi(os.path.join(parent_folder,'gemini_receipts.ui'), self)
        self.setWindowIcon(QtGui.QIcon(os.path.join(parent_folder, 'icon.ico')))

        self.stopped = True
        self.thread = QThread()

        self.setWindowTitle('Gemini Receipts')

        self.settings_file = get_config_file()

        self.api_key = self.load_settings()
        if self.api_key:
            self.api_key_text.setText(self.api_key)
        

        # Folder containing receipt images
        self.input_folder = None

        # Output CSV
        self.output_csv = None

        # Connect buttons
        self.rec_button.clicked.connect(self.select_receipt_folder)
        self.csv_button.clicked.connect(self.select_csv_folder)
        self.run_button.clicked.connect(self.button_pressed)

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                self.settings_dict = json.load(f)
                self.api_key = self.settings_dict['key']
                return self.settings_dict['key']

        except Exception as eee:
            print('Cannot load settings')
            print(eee)
            return False

    def save_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                new_dict = json.load(f)
                new_dict['key'] = self.api_key_text.text()
        except:
            new_dict = {
                "key": self.api_key_text.text()
            }

        j = json.dumps(new_dict, indent=4)
        with open(self.settings_file, 'w') as f:
            print(j, file=f)

        self.update_log('Saved API key to settings\n', 'green')

    def button_pressed(self):
        
        if self.input_folder != None and self.output_csv != None:
            if not self.api_key and self.api_key_text.text() != '':
                self.api_key = self.api_key_text.text()
                self.save_settings()
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.run()
        else:
            pass



    def select_csv_folder(self):
        self.output_csv = QtWidgets.QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")[0]
        self.csv_line.setText(self.output_csv)
        self.update_log(f"Output CSV set to: {self.output_csv}\n")

    
    def select_receipt_folder(self):
        self.input_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Receipt Directory")
        self.rec_line.setText(self.input_folder)
        self.update_log(f"Input folder set to: {self.input_folder}\n")

    def run(self):
        if self.stopped:
            self.stopped = False
            self.run_button.setText('STOP')
            self.thread = QThread()
            self.worker = Worker(
                self,
                self.model,
                self.output_csv,
                self.input_folder
            )
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.update_log)
            self.thread.start()
            return
        elif self.stopped == False:
            self.stopped = True
            self.run_button.setText('Stopping...')
            self.run_button.setEnabled(False)
            self.worker.finished.emit()
            return


    def update_log(self, message, color=None):
        if color:
            self.logs.append(f'<p style="color:{color};">'+message+'</p> ')
        else:
            self.logs.append(message)  # Append message to log view
        scroll_bar = self.logs.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    GRC = gemini_receipt()
    GRC.show()
    sys.exit(app.exec())