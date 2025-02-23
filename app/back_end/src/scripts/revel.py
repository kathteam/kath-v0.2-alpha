import os
import csv
import sqlite3
import logging
import argparse

from tqdm import tqdm

logger = logging.getLogger(__name__)

class RevelTable:
    """REVEL table class for SQLite database."""

    @staticmethod
    def init_table(file_path: str, db_path: str) -> None:
        """Convert valid rows of REVEL CSV (6GB) into a SQLite database."""
        
        if os.path.exists(db_path):
            logger.error(f"Sqlite database already exists at {os.path.abspath(db_path)}")
            raise FileExistsError(f"SQLite database already exists at {os.path.abspath(db_path)}")
        
        # Initialize database with revel table
        logger.debug("Initializing revel table...")
        with sqlite3.connect(db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL2')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS revel (
                    chr TEXT,
                    grch38_pos INTEGER,
                    ref TEXT,
                    alt TEXT,
                    REVEL REAL,
                    PRIMARY KEY (chr, grch38_pos, ref, alt)
                )
                '''
            )
            conn.commit()

            # Chunk size
            chunk_size = 100_000
            chunk = []
            
            logger.debug("Beginning revel file processing...")
            with tqdm(desc = "Processing rows", unit = "Rows", unit_scale = True) as pbar:
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for idx, row in enumerate(reader):
                        # Chunk border
                        if (idx % chunk_size == 0):
                            if chunk:
                                conn.execute('BEGIN TRANSACTION')
                                conn.executemany('INSERT OR IGNORE INTO revel VALUES (?,?,?,?,?)', chunk)
                                conn.commit()
                                chunk = []
                            # Progress bar update
                            pbar.update(chunk_size)
                        # Stop if chromosome is greater than 6
                        if row['chr'] > '6':
                            break
                        # Skip invalid chromosomes
                        if row['chr'] != '6' or row['grch38_pos'] == '.':
                            continue
                        try:
                            chunk.append((
                                row['chr'],
                                int(row['grch38_pos']),
                                row['ref'],
                                row['alt'],
                                float(row['REVEL'])
                            ))
                        except Exception as e:
                            logger.error(f"Error in processing row (Possibly not supporting \"X,Y ... \" chromosome types): {e}")
                # Leftover chunk
                if chunk:
                    conn.execute('BEGIN TRANSACTION')
                    conn.executemany('INSERT OR IGNORE INTO revel VALUES (?,?,?,?,?)', chunk)
                    conn.commit()
                    # Final progress bar update
                    pbar.update(len(chunk))

            logger.debug("Creating revel table indexes...")
            conn.execute('CREATE INDEX idx_pos ON revel(grch38_pos)')
            conn.execute('CREATE INDEX idx_chr_pos ON revel(chr, grch38_pos)')
            logger.info(f"Revel table initialized. Sqlite database at {os.path.abspath(db_path)}")

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description = "Sqlite database revel tabel initiation script.")
    parser.add_argument("file_path", help = "Revel file path which contains data", type = str)
    parser.add_argument("db_path", help = "Sqlite database file path in which create the REVEL table", type = str)
    parser.add_argument("-o", "--overwrite", help = "Overwrite the database file if it already exists", action = "store_true")
    parser.add_argument("-l", "--log_level", help = "Set the logging level (default: info)", type = str, default = "info", choices = ["debug", "info", "warning", "error", "critical"])
    args = parser.parse_args()

    # Logging configuration
    logging.basicConfig(
        level = getattr(logging, args.log_level.upper(), logging.INFO),
        format = "%(asctime)s - %(levelname)s - %(message)s",
    )

    # Paths
    revel_file_path = args.file_path
    revel_db_path = args.db_path

    # Cleanup
    if os.path.exists(revel_db_path) and args.overwrite:
        os.remove(revel_db_path)

    # Initialize the database with revel table
    RevelTable.init_table(file_path = revel_file_path, db_path = revel_db_path)