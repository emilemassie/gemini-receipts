# Gemini Receipts

Gemini Receipts is a desktop application that uses Google's Gemini AI model to extract structured receipt data from images and save it into a CSV file.  
It supports batch processing of images and provides a simple user interface built with PyQt6.

## Features

- Extracts vendor, location, category, subtotal, taxes, tip, total, and date from receipt images.
- Supports multiple receipts per image.
- Saves the extracted data into a clean CSV file.
- Stores your Gemini API key securely in your user configuration directory.
- Start/Stop processing at any time.
- Logs progress and model responses in real time.

## Requirements

- Python 3.9+
- Google Generative AI Python SDK (`google-generativeai`)
- Pillow (`PIL`)
- pandas
- PyQt6
- appdirs

You can install the dependencies using:

```bash
pip install -r requirements.txt
```

Example `requirements.txt`:

```
google-generativeai
pillow
pandas
pyqt6
appdirs
```

## Getting a Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account if necessary.
3. Click on **"Create API Key"**.
4. Copy the generated API key — you'll need it to configure this application.
5. Paste the API key into the app when prompted on first launch.

**Note:** Usage of the API might require billing to be enabled on your Google Cloud account depending on the quota.

## Setup

1. Clone this repository or copy the files.
2. Make sure you have a Gemini API key from Google.
3. Launch `gemini_receipts.py`.
4. On first launch, enter your Gemini API key in the interface and it will be saved for future sessions.

## Usage

1. **Select a Folder** — Choose the folder containing receipt images (`.png`, `.jpg`, `.jpeg`, `.webp` formats are supported).
2. **Select CSV Output** — Choose where to save the generated CSV file.
3. **Click "Process"** — The app will process each image, extract the receipt data using the Gemini model, and save it to the CSV file.
4. **Stop if needed** — You can click "Stop" anytime to halt processing.

## Example JSON Extraction Prompt

The app sends a prompt asking the model to return a list of receipts in JSON format:

```json
[
    {
        "vendor": "Starbucks",
        "location": "Montreal",
        "category": "restaurant",
        "subtotal": "50.95",
        "taxes": "9.76",
        "tip": "3.55",
        "total": "64.26",
        "date": "2024-02-13"
    },
    {
        "vendor": "Target",
        "location": "Toronto",
        "category": "clothing",
        "subtotal": "70.44",
        "taxes": "12.28",
        "tip": "",
        "total": "86.72",
        "date": "2024-12-30"
    }
]
```

Only clean JSON is accepted — any other format will cause the entry to be skipped.

## Configuration File

The API key and settings are saved in your user config directory, e.g., on Windows:

```
C:/Users/YourUsername/AppData/Local/gemeni-receipts/gemeni-receipts/YourUsername_settings.conf
```

## Notes

- Make sure your receipt images are clear and readable for better extraction accuracy.
- A `.ui` file (`gemini_receipts.ui`) and an icon file (`icon.ico`) are required for the UI to work correctly.
- Only the Gemini 1.5 Flash model is currently used.

## License

MIT License.