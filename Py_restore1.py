import os
import logging

# Constants
TARGET_DATA_PATH = r"D:\Dedupe_Project\Library"  # Path where chunks are stored
RESTORE_PATH = r"D:\Dedupe_Project\Restore"     # Path where restored files will be saved

# Create necessary directories
os.makedirs(RESTORE_PATH, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(RESTORE_PATH, 'restore.log')),
        logging.StreamHandler()
    ]
)

def restore_file(metadata_file):
    """
    Restores a file based on the metadata file.

    Args:
        metadata_file (str): Path to the metadata file containing chunk hashes and paths.

    Returns:
        str: Path to the restored file.
    """
    try:
        # Validate metadata file existence
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Metadata file does not exist: {metadata_file}")

        # Determine the restored file path
        restored_file_name = os.path.basename(metadata_file).replace(".meta", "")
        restored_file_path = os.path.join(RESTORE_PATH, restored_file_name)
        os.makedirs(os.path.dirname(restored_file_path), exist_ok=True)

        # Open the metadata file and reconstruct the original file
        with open(metadata_file, 'r') as meta_file, open(restored_file_path, 'wb') as restored_file:
            for line in meta_file:
                chunk_hash, chunk_path = line.strip().split(',')
                chunk_path = chunk_path.strip()

                # Verify if the chunk exists in the Library folder
                if not os.path.exists(chunk_path):
                    logging.warning(f"Missing chunk: {chunk_hash} at {chunk_path}")
                    continue

                # Read and write the chunk data to reconstruct the original file
                with open(chunk_path, 'rb') as chunk_file:
                    chunk_data = chunk_file.read()
                    restored_file.write(chunk_data)

        logging.info(f"Restored file: {restored_file_path}")
        return restored_file_path

    except Exception as e:
        logging.error(f"Error restoring file from metadata {metadata_file}: {e}")
        return None

def run_restore(metadata_path):
    """
    Main function to restore files using a metadata file.

    Args:
        metadata_path (str): Path to the metadata file.
    
    Returns:
        dict: Status and message of the restoration process.
    """
    try:
        # Validate input
        if not metadata_path or not os.path.exists(metadata_path):
            return {"status": "error", "message": f"Invalid metadata path: {metadata_path}. File does not exist."}

        if not os.access(metadata_path, os.R_OK):
            return {"status": "error", "message": f"Access denied for metadata file: {metadata_path}. Check permissions."}

        # Restore the file using the provided metadata
        restored_file = restore_file(metadata_path)
        
        if restored_file:
            return {"status": "success", "message": f"Restore completed successfully. Restored file: {restored_file}"}
        else:
            return {"status": "error", "message": "Restore failed. Check logs for details."}

    except Exception as e:
        logging.error(f"Error in run_restore: {e}")
        return {"status": "error", "message": str(e)}
