# import os
# import json
# import logging
# import sqlite3
# from datetime import datetime

# logger = logging.getLogger(__name__)

# def setup_logging():
#     """Set up logging for the application."""
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.StreamHandler(),
#             logging.FileHandler('app.log')
#         ]
#     )

# def load_profiles_config():
#     """Load LinkedIn profiles configuration from file."""
#     config_path = os.path.join('data', 'profiles.json')
    
#     if not os.path.exists(config_path):
#         logger.error(f"Profile configuration file not found at {config_path}")
#         return None
    
#     try:
#         with open(config_path, 'r', encoding='utf-8') as file:
#             return json.load(file)
#     except json.JSONDecodeError as e:
#         logger.error(f"Error parsing profiles configuration: {e}")
#         return None

# def initialize_database():
#     """Initialize SQLite database for storing LinkedIn posts data."""
#     db_path = os.path.join('data', 'posts_database.db')
    
#     # Ensure data directory exists
#     os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
    
#     # Create tables if they don't exist
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS posts (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             profile_url TEXT,
#             profile_name TEXT,
#             post_url TEXT UNIQUE,
#             post_content TEXT,
#             publish_date TEXT,
#             likes INTEGER,
#             comments INTEGER,
#             shares INTEGER,
#             collected_at TEXT
#         )
#     ''')
    
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS generated_posts (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             content TEXT,
#             hashtags TEXT,
#             generated_at TEXT,
#             feedback_score INTEGER,
#             feedback_text TEXT,
#             scheduled_time TEXT,
#             published INTEGER DEFAULT 0
#         )
#     ''')
    
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS analytics (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             metric_name TEXT,
#             metric_value REAL,
#             recorded_at TEXT
#         )
#     ''')
    
#     conn.commit()
#     conn.close()
    
#     logger.info(f"Database initialized at {db_path}")
#     return db_path

# def get_db_connection():
#     """Get a connection to the SQLite database."""
#     db_path = os.path.join('data', 'posts_database.db')
#     return sqlite3.connect(db_path)

# def save_generated_post(content, hashtags):
#     """Save a generated post to the database."""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute(
#         "INSERT INTO generated_posts (content, hashtags, generated_at) VALUES (?, ?, ?)",
#         (content, hashtags, datetime.now().isoformat())
#     )
    
#     post_id = cursor.lastrowid
#     conn.commit()
#     conn.close()
    
#     return post_id

# # Add the missing function that's being imported in app.py
# def save_post_to_db(content, hashtags):
#     """Save a post to the database (alias for save_generated_post)."""
#     return save_generated_post(content, hashtags)

# def update_post_feedback(post_id, feedback_score, feedback_text):
#     """Update feedback for a generated post."""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute(
#         "UPDATE generated_posts SET feedback_score = ?, feedback_text = ? WHERE id = ?",
#         (feedback_score, feedback_text, post_id)
#     )
    
#     conn.commit()
#     conn.close()

# def schedule_post(post_id, scheduled_time):
#     """Schedule a post for publishing."""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute(
#         "UPDATE generated_posts SET scheduled_time = ? WHERE id = ?",
#         (scheduled_time, post_id)
#     )
    
#     conn.commit()
#     conn.close()

# def ensure_directories():
#     """Ensure all required directories exist."""
#     directories = [
#         'data',
#         'data/generated_posts',
#     ]
    
#     for directory in directories:
#         os.makedirs(directory, exist_ok=True)
#         logger.info(f"Directory exists or created: {directory}")
import os
import json
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_logging():
    """Set up logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )

def load_profiles_config():
    """Load LinkedIn profiles configuration from file."""
    config_path = os.path.join('data', 'profiles.json')
    
    if not os.path.exists(config_path):
        logger.error(f"Profile configuration file not found at {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing profiles configuration: {e}")
        return None

def initialize_database():
    """Initialize SQLite database for storing LinkedIn posts data."""
    db_path = os.path.join('data', 'posts_database.db')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
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

def get_db_connection():
    """Get a connection to the SQLite database."""
    db_path = os.path.join('data', 'posts_database.db')
    return sqlite3.connect(db_path)

def save_generated_post(content, hashtags, profile=None, topic=None, tone=None):
    """Save a generated post to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO generated_posts 
               (content, hashtags, generated_at, profile, topic, tone) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (content, hashtags, datetime.now().isoformat(), profile, topic, tone)
        )
        
        post_id = cursor.lastrowid
        conn.commit()
        return post_id
    except Exception as e:
        logger.error(f"Error saving generated post: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def save_post_to_db(content, hashtags, profile=None, topic=None, tone=None):
    """Save a post to the database (enhanced version of save_generated_post)."""
    return save_generated_post(content, hashtags, profile, topic, tone)

def update_post_feedback(post_id, feedback_score, feedback_text):
    """Update feedback for a generated post."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE generated_posts SET feedback_score = ?, feedback_text = ? WHERE id = ?",
            (feedback_score, feedback_text, post_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating post feedback: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def schedule_post(post_id, scheduled_time):
    """Schedule a post for publishing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE generated_posts SET scheduled_time = ? WHERE id = ?",
            (scheduled_time, post_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error scheduling post: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        'data',
        'data/generated_posts',
        'src'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory exists or created: {directory}")