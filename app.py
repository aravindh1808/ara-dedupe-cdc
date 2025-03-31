from flask import Flask, render_template, request, jsonify
import os
import sqlite3
from Py_Dedupe1 import run_deduplication  # Import deduplication logic
from Py_restore1 import run_restore  # Import deduplication logic
app = Flask(__name__)

HASH_DB_PATH = r"D:\Dedupe_Project\DDB\hash_keys.db"  # Path to the SQLite database

@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')
    
@app.route('/db_table', methods=['GET'])
def db_table():
    """Fetch and display database table contents."""
    try:
        conn = sqlite3.connect(HASH_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chunks")  # Query all rows from the 'chunks' table
        rows = cursor.fetchall()
        conn.close()

        # Convert rows into a list of dictionaries for easier rendering in HTML
        data = [{"hash": row[0], "chunk_path": row[1]} for row in rows]
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/backup', methods=['POST'])
def backup():
    """Handle Backup operation."""
    source_path = request.json.get('sourcePath')  # Use JSON input

    # Validate source path
    if not source_path:
        return jsonify({"status": "error", "message": "Source path cannot be empty."})
    if not os.path.exists(source_path):
        return jsonify({"status": "error", "message": f"Invalid source path: {source_path}. Directory does not exist."})
    if not os.access(source_path, os.R_OK):
        return jsonify({"status": "error", "message": f"Access denied for source path: {source_path}. Check permissions."})

    try:
        global SOURCE_PATH
        SOURCE_PATH = source_path  # Dynamically update SOURCE_PATH

        # Run deduplication and get stats
        stats = run_deduplication()

        # Return success with deduplication summary
        return jsonify({
            "status": "success",
            "message": f"Backup completed for {source_path}",
            "deduplicationSummary": stats
        })
    except Exception as e:
        logging.error(f"Error during backup: {e}")
        return jsonify({"status": "error", "message": str(e)})



@app.route('/restore', methods=['POST'])
def restore():
    """Handle restore operation."""
    metadata_path = request.json.get('metadataPath')

    if not metadata_path:
        return jsonify({"status": "error", "message": "Metadata path cannot be empty."})
    if not os.path.exists(metadata_path):
        return jsonify({"status": "error", "message": f"Invalid Metadata path: {metadata_path}. Directory does not exist."})
    if not os.access(metadata_path, os.R_OK):
        return jsonify({"status": "error", "message": f"Access denied for Metadata path: {metadata_path}. Check permissions."})

    try:
        global METADATA_PATH
        METADATA_PATH = metadata_path  # Dynamically update metadata_PATH
        
        run_restore(metadata_path)  # Run rehydrate logic
        return jsonify({"status": "success", "message": f"Restore completed for {metadata_path}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
