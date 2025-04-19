import os
import sqlite3
import logging
from src.utils import ensure_directories

logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize SQLite database for storing LinkedIn posts data."""
    # Ensure directories exist
    ensure_directories()
    
    db_path = os.path.join('data', 'posts_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_url TEXT,
            profile_name TEXT,
            post_url TEXT UNIQUE,
            post_content TEXT,
            publish_date TEXT,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            collected_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            hashtags TEXT,
            generated_at TEXT,
            feedback_score INTEGER,
            feedback_text TEXT,
            scheduled_time TEXT,
            published INTEGER DEFAULT 0,
            profile TEXT,
            topic TEXT,
            tone TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT,
            metric_value REAL,
            recorded_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database initialized at {db_path}")
    return db_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_path = initialize_database()
    print(f"Database initialized at: {db_path}")