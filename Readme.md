# Expense Tracker AI - Professional Edition

Expense Tracker AI is a sophisticated Python application designed to automate the extraction of key information (such as amount and date) from receipts and invoices. The app leverages AI-powered analysis, organizes files, stores extracted data in a SQLite database, and features a professional-grade graphical user interface built with CustomTkinter.

---

## Features

- **AI-Powered Data Extraction**: Uses Google's Gemini AI to automatically pull data from images and PDFs.
- **Modern UI**: A clean, professional user interface with a dark theme.
- **Live Statistics**: A "dashboard" view that provides real-time stats on your expenses.
- **Image/PDF Preview**: Instantly preview the original receipt file directly in the app.
- **Data Editing**: Manually edit or correct extracted data with a simple double-click.
- **CSV and File Export**: Export your expense data to a CSV file or export all processed files with new, organized names.
- **Secure Configuration**: Uses a `.env` file for secure API key management and a `config.json` for persistent UI settings.

---

## Screenshots

*(Here you can add a new screenshot of the professional UI)*

`![UI Screenshot](assets/new_ui_screenshot.png)`

---

## Project Structure

```
Expense_Tracker_app-main/
├── .env
├── requirements.txt
├── config/
│   └── app_settings.json
├── inputs/
│   └── (Your receipt files go here)
├── outputs/
│   ├── DB/
│   │   └── image_data.db
│   ├── logs/
│   └── export/
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   └── processor.py
│   ├── UI/
│   │   ├── __init__.py
│   │   └── tk_UI.py
│   └── utils/
│       ├── __init__.py
│       ├── db_manager.py
│       └── logger.py
└── Readme.md
```

---

## Setup

1.  **Clone the repository:**
    ```sh
    git clone <your-repo-url>
    cd Expense_Tracker_app-main
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # On Windows
    python -m venv .venv
    .venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
    
4.  **Install Poppler (for PDF Previews on Windows):**
    - Download the latest Poppler binary from [this link](https://github.com/oschwartz10612/poppler-windows/releases/).
    - Extract it to a location like `C:\Program Files\poppler`.
    - Add the `bin` directory inside the extracted folder to your system's PATH environment variable.

5.  **Configure your API Key:**
    - Create a file named `.env` in the root of the project.
    - Add your Google Gemini API key to it like this:
      ```
      GEMINI_API_KEY=YOUR_API_KEY_HERE
      ```

---

## Usage

1.  **Place your receipt files** (images or PDFs) into the `inputs/` directory.

2.  **Run the application:**
    ```sh
    python src/main.py
    ```
    
3.  **First-time setup:** The app may prompt you to configure the source and database paths. These settings will be saved for future use.

4.  **Use the UI** to analyze files, view data, and export your results.

---
