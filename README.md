# VARIABLE BLOCK FACTOR DATA DEDUPLICATION FOR PROTECTING LARGER DATASETS

## Project Overview
This project implements a **Variable Block Length Deduplication** system designed to optimize storage by eliminating redundant data blocks. The system uses content-defined chunking techniques and maintains metadata for efficient data restoration. It is built using Python and Flask for a web interface, SQLite for metadata storage, and logging for detailed process tracking.

---

## Features
- **Variable-Size Content-Defined Chunking**: Dynamically adjusts chunk sizes to optimize deduplication efficiency.
- **Data Deduplication**:
  - Identifies and removes duplicate data blocks.
  - Stores unique chunks in a library for reuse.
- **Backup System**:
  - Processes files from a source directory.
  - Generates metadata for each file to enable restoration.
- **Restore System**:
  - Reconstructs original files using stored chunks and metadata.
- **Web Interface**:
  - Provides endpoints for backup, restore, and database inspection.

---

## File Descriptions
### 1. `index.html`
- The main HTML page for the web interface.

### 2. `app.py`
- Flask-based web application providing RESTful APIs:
  - `/`: Renders the main page.
  - `/db_table`: Fetches and displays the database table contents.
  - `/backup`: Initiates the deduplication process for a given source path.
  - `/restore`: Restores files using metadata.

### 3. `Py_Dedupe1.py`
- Core deduplication logic:
  - Implements variable-size chunking using content-defined techniques.
  - Manages SQLite database to store chunk hashes and paths.
  - Logs detailed deduplication statistics, including:
    - Total files processed
    - Total data size
    - New chunks written
    - Deduplication ratio

### 4. `Py_restore1.py`
- Restoration logic:
  - Reconstructs original files from metadata and stored chunks.
  - Handles missing chunks gracefully with warnings in logs.

---


### Prerequisites
1. Python 3.x installed on your system.
2. Install required dependencies:
pip install flask
pip install sqllite

### Required File Paths
SOURCE_PATH = r"D:\Dedupe_Project\Source"

TARGET_DATA_PATH = r"D:\Dedupe_Project\Library"

TARGET_METADATA_PATH = r"D:\Dedupe_Project\BackupSets"

HASH_DB_PATH = r"D:\Dedupe_Project\DDB\hash_keys.db"

RESTORE_PATH = r"D:\Dedupe_Project\Restore"

### Folder Structure
├── app.py # Flask application with RESTful APIs

├── Py_Dedupe1.py # Deduplication logic

├── Py_restore1.py # Restoration logic

├── templates/

│ └── index.html # Web interface HTML file

└── DDB/ # SQLite database for hash keys (auto-created)

## How to Run
Use PowerShell:

1. --- Set Environment Variable ---
$env:FLASK_APP = "D:\dedupe_project\project\app.py"

2. --- Start Server using Flask ---
flask run

3. Now open http://127.0.0.1:5000/ in Web console.

4. Input Source Path and click Backup to run Backup

5. Input Metadata path and click Restore to restore the file

6. Click "Load Table" to view contents the list of chunks.
