import os
import hashlib
import sqlite3
from datetime import datetime
import logging

# Constants
SOURCE_PATH = r"D:\Dedupe_Project\Source"
TARGET_DATA_PATH = r"D:\Dedupe_Project\Library"
TARGET_METADATA_PATH = r"D:\Dedupe_Project\BackupSets"
HASH_DB_PATH = r"D:\Dedupe_Project\DDB\hash_keys.db"
MIN_CHUNK_SIZE = 4096  # Minimum chunk size (4 KB)
AVG_CHUNK_SIZE = 8192  # Average chunk size (8 KB)
MAX_CHUNK_SIZE = 16384  # Maximum chunk size (16 KB)

# Create necessary directories
os.makedirs(SOURCE_PATH, exist_ok=True)
os.makedirs(TARGET_DATA_PATH, exist_ok=True)
os.makedirs(TARGET_METADATA_PATH, exist_ok=True)
os.makedirs(os.path.dirname(HASH_DB_PATH), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(TARGET_METADATA_PATH, 'dedupe.log')),
        logging.StreamHandler()
    ]
)

def create_hash_db():
    conn = sqlite3.connect(HASH_DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS chunks
                    (hash TEXT PRIMARY KEY, chunk_path TEXT)''')
    conn.commit()
    return conn

def hash_chunk(data):
    return hashlib.sha256(data).hexdigest()

def write_chunk(chunk_hash, data):
    chunk_path = os.path.join(TARGET_DATA_PATH, chunk_hash)
    if not os.path.exists(chunk_path):
        with open(chunk_path, 'wb') as f:
            f.write(data)
        logging.debug(f"Created new chunk: {chunk_hash} ({len(data)} bytes)")
        return True  # Indicates a new chunk was written
    return False  # Indicates the chunk already exists

def variable_size_chunking(data):
    """Perform variable-size content-defined chunking."""
    chunks = []
    i = 0
    data_len = len(data)
    fingerprint = 0

    while i < data_len:
        start = i
        end = min(i + AVG_CHUNK_SIZE, data_len)

        for j in range(start + MIN_CHUNK_SIZE, end):
            fingerprint = ((fingerprint << 1) + data[j]) & 0xFFFFFFFF
            if (fingerprint & (2**12 - 1)) == 0 or j - start >= MAX_CHUNK_SIZE:
                chunks.append((start, j - start + 1))
                i = j + 1
                break
        else:
            chunks.append((start, end - start))
            i = end

    return chunks

def process_file(file_path, conn, stats):
    chunks = []
    try:
        file_size = os.path.getsize(file_path)
        stats['total_data_size'] += file_size  # Add file size to total data size
        stats['total_files'] += 1  # Increment file count

        with open(file_path, 'rb') as f:
            data = f.read()
            if not data:
                logging.warning(f"File is empty: {file_path}")
                return []

            chunk_offsets = variable_size_chunking(data)

            for offset, size in chunk_offsets:
                chunk = data[offset:offset + size]
                if len(chunk) == 0:
                    continue

                stats['total_chunks'] += 1  # Increment total chunks processed

                chunk_hash = hash_chunk(chunk)
                cursor = conn.cursor()
                cursor.execute("SELECT chunk_path FROM chunks WHERE hash=?", (chunk_hash,))
                result = cursor.fetchone()

                if result:
                    chunks.append((chunk_hash, result[0]))
                else:
                    is_new_chunk = write_chunk(chunk_hash, chunk)
                    if is_new_chunk:
                        stats['new_chunks'] += 1  # Increment new chunks counter
                        stats['new_data_size'] += len(chunk)  # Add size of new chunk to total
                    cursor.execute("INSERT INTO chunks VALUES (?,?)", (chunk_hash, os.path.join(TARGET_DATA_PATH, chunk_hash)))
                    chunks.append((chunk_hash, os.path.join(TARGET_DATA_PATH, chunk_hash)))

            conn.commit()

    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        conn.rollback()
        return []

    return chunks

def run_deduplication():
    conn = create_hash_db()
    stats = {
        'total_files': 0,
        'total_data_size': 0,
        'new_chunks': 0,
        'new_data_size': 0,
        'total_chunks': 0
    }

    backup_set_name = f"BackupSet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_set_path = os.path.join(TARGET_METADATA_PATH, backup_set_name)
    os.makedirs(backup_set_path, exist_ok=True)

    for root, _, files in os.walk(SOURCE_PATH):
        for file in files:
            source_file = os.path.join(root, file)
            logging.info(f"Processing file: {source_file}")
            chunks = process_file(source_file, conn, stats)
            if not chunks:
                continue

            rel_path = os.path.relpath(source_file, SOURCE_PATH)
            meta_file_path = os.path.join(backup_set_path, rel_path + ".meta")
            os.makedirs(os.path.dirname(meta_file_path), exist_ok=True)

            with open(meta_file_path, 'w') as meta_file:
                for chunk_hash, chunk_path in chunks:
                    meta_file.write(f"{chunk_hash},{chunk_path}\n")

            logging.info(f"Created metadata for {rel_path} with {len(chunks)} chunks")

    conn.close()

    dedup_ratio_percentage = (
        ((1 - (stats['new_data_size'] / stats['total_data_size'])) * 100)
        if stats['total_data_size'] > 0 else None
    )

    stats['dedup_ratio_percentage'] = dedup_ratio_percentage

    logging.info("\n=== Deduplication Summary ===")
    logging.info(f"Total Files Backed Up: {stats['total_files']}")
    logging.info(f"Total Size of Data: {stats['total_data_size']} bytes")
    logging.info(f"New Data Blocks Written: {stats['new_chunks']}")
    logging.info(f"Total Chunks Processed: {stats['total_chunks']}")
    if dedup_ratio_percentage is not None:
        logging.info(f"Deduplication Ratio: {dedup_ratio_percentage:.2f}%")
    else:
        logging.info("Deduplication Ratio: N/A (No new data written)")

    return stats


if __name__ == "__main__":
    run_deduplication()
