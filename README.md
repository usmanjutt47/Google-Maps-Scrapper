# 🗺️ Google Maps Scraper with Excel Export

A powerful, automated web scraper built with Python and Playwright to extract local business leads directly from Google Maps into formatted Excel (`.xlsx`) files.

---

## 🌟 Key Features

- 📍 **Comprehensive Business Data**: Extracts **Name**, **Email**, **Category**, **Phone Number**, and **Website**.
- 📧 **Smart Email Extraction**: Scrapes emails from Google Maps cards and automatically visits business websites (including `/contact` and `/about` pages) to find email addresses.
- 📊 **Formatted Excel Export**: Saves clean `.xlsx` spreadsheets ready for outreach or CRM integration.
- 🔄 **Smart Append & Deduplication**: Automatically appends new search results to existing Excel files while filtering out duplicate entries based on Name, Phone Number, and Website.
- ⚙️ **Customizable CLI**: Flexible command-line options for search queries, target result counts, custom output paths, and overwrite flags.

---

## 📋 Prerequisites & Initial Setup (Beginner Guide)

If you are using this project for the first time, follow these step-by-step instructions.

### Step 1: Install Python

Ensure you have Python 3.8 or higher installed on your computer.

#### 🪟 Windows:
1. Download the latest Python installer from [python.org/downloads](https://www.python.org/downloads/).
2. Run the installer.
3. ⚠️ **IMPORTANT**: Check the box that says **"Add python.exe to PATH"** at the bottom of the first screen before clicking "Install Now".
4. Open **Command Prompt** or **PowerShell** and verify installation:
   ```cmd
   python --version
   ```

#### 🍎 macOS:
Install via [Homebrew](https://brew.sh/):
```bash
brew install python
python3 --version
```

#### 🐧 Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

---

### Step 2: Download / Clone the Repository

Open your terminal or PowerShell and run:

```bash
git clone https://github.com/usmanjutt47/Google-Maps-Scrapper.git
cd Google-Maps-Scrapper
```

---

### Step 3: Create a Virtual Environment (Recommended)

Creating a virtual environment isolates project dependencies so they don't interfere with system software.

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

*(You will see `(venv)` appear at the beginning of your terminal prompt).*

---

### Step 4: Install Dependencies & Playwright Browser

Install the required Python packages and the Chromium browser engine used by Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🚀 How to Run the Scraper

### 1. Basic Usage (Default Search)
Runs with the default search query (`"turkish stores in toronto Canada"`) and scrapes 1 result into `result.xlsx`:

```bash
python main.py
```

### 2. Custom Search & Total Results
Scrape 10 coffee shops in New York:

```bash
python main.py -s "coffee shops in New York" -t 10
```

### 3. Specify Custom Output File Name
Save results to a custom file named `toronto_gyms.xlsx`:

```bash
python main.py -s "gyms in Toronto" -t 15 -o toronto_gyms.xlsx
```

### 4. Overwrite Existing File
By default, running a scrape on an existing output file appends new data and removes duplicates. To replace the existing file completely, add `--overwrite`:

```bash
python main.py -s "restaurants in London" -t 20 -o London_food.xlsx --overwrite
```

---

## ⚙️ Command-Line Arguments Reference

| Flag / Option | Full Option | Description | Default Value |
| :--- | :--- | :--- | :--- |
| `-s` | `--search` | Search query to execute on Google Maps | `"turkish stores in toronto Canada"` |
| `-t` | `--total` | Total number of listings/places to scrape | `1` |
| `-o` | `--output` | Output path for the Excel spreadsheet (`.xlsx`) | `"result.xlsx"` |
| N/A | `--overwrite` | Overwrite the target Excel file instead of appending | `False` |

---

## 📊 Output File Format

The generated Excel file contains the following columns in order:

| Name | Email | Category | Phone Number | Website |
| :--- | :--- | :--- | :--- | :--- |
| Example Business | info@example.com | Supermarket | 14165550199 | https://example.com |

---

## ❓ Frequently Asked Questions (FAQ) & Troubleshooting

<details>
<summary><b>Q: 'python' is not recognized as an internal or external command on Windows</b></summary>

> **Fix**: Python was installed without checking **"Add python.exe to PATH"**. Re-run the Python installer, select "Modify", and check "Add Python to PATH". Alternatively, try running with `py main.py`.
</details>

<details>
<summary><b>Q: Playwright executable / browser error</b></summary>

> **Fix**: Run `playwright install chromium` in your terminal to ensure the required headless browser binary is downloaded.
</details>

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).