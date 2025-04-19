# import logging
# import sqlite3
# from datetime import datetime, timedelta
# import threading
# import time
# import json
# import requests
# from src.utils import get_db_connection

# logger = logging.getLogger(__name__)

# class PostScheduler:
#     def __init__(self):
#         """Initialize the post scheduler."""
#         self.conn = get_db_connection()
#         self._ensure_tables_exist()
#         self._start_scheduler_thread()
    
#     def _ensure_tables_exist(self):
#         """Ensure necessary database tables exist."""
#         try:
#             cursor = self.conn.cursor()
            
#             # Create scheduled_posts table if not exists
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS scheduled_posts (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     post_id INTEGER NOT NULL,
#                     scheduled_time DATETIME NOT NULL,
#                     status TEXT DEFAULT 'Scheduled',
#                     FOREIGN KEY (post_id) REFERENCES generated_posts (id)
#                 )
#             """)
            
#             self.conn.commit()
#             logger.info("Scheduler tables initialized")
            
#         except Exception as e:
#             logger.error(f"Error initializing scheduler tables: {e}")
    
#     def schedule_post(self, post_id, scheduled_time):
#         """Schedule a post for future publishing.
        
#         Args:
#             post_id: ID of the post to schedule
#             scheduled_time: Datetime when post should be published
            
#         Returns:
#             Boolean indicating success
#         """
#         try:
#             # Validate inputs
#             if not isinstance(post_id, int) or post_id <= 0:
#                 logger.error(f"Invalid post ID: {post_id}")
#                 return False
            
#             if not isinstance(scheduled_time, datetime):
#                 logger.error(f"Invalid scheduled time: {scheduled_time}")
#                 return False
            
#             # Format datetime for SQLite
#             scheduled_time_str = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
            
#             # Insert into scheduled_posts table
#             cursor = self.conn.cursor()
#             cursor.execute(
#                 """
#                 INSERT INTO scheduled_posts (post_id, scheduled_time, status)
#                 VALUES (?, ?, 'Scheduled')
#                 """,
#                 (post_id, scheduled_time_str)
#             )
            
#             self.conn.commit()
#             schedule_id = cursor.lastrowid
            
#             logger.info(f"Post {post_id} scheduled for {scheduled_time_str}, schedule ID: {schedule_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error scheduling post: {e}")
#             return False
    
#     def reschedule_post(self, schedule_id, new_scheduled_time):
#         """Reschedule a previously scheduled post.
        
#         Args:
#             schedule_id: ID of the schedule entry
#             new_scheduled_time: New datetime for publishing
            
#         Returns:
#             Boolean indicating success
#         """
#         try:
#             # Validate inputs
#             if not isinstance(schedule_id, int) or schedule_id <= 0:
#                 logger.error(f"Invalid schedule ID: {schedule_id}")
#                 return False
            
#             if not isinstance(new_scheduled_time, datetime):
#                 logger.error(f"Invalid new scheduled time: {new_scheduled_time}")
#                 return False
            
#             # Format datetime for SQLite
#             new_time_str = new_scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
            
#             # Update scheduled_posts table
#             cursor = self.conn.cursor()
#             cursor.execute(
#                 """
#                 UPDATE scheduled_posts
#                 SET scheduled_time = ?, status = 'Scheduled'
#                 WHERE id = ? AND status != 'Published'
#                 """,
#                 (new_time_str, schedule_id)
#             )
            
#             self.conn.commit()
            
#             if cursor.rowcount == 0:
#                 logger.warning(f"No schedule with ID {schedule_id} found or already published")
#                 return False
            
#             logger.info(f"Schedule {schedule_id} updated to {new_time_str}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error rescheduling post: {e}")
#             return False
    
#     def cancel_post(self, schedule_id):
#         """Cancel a scheduled post.
        
#         Args:
#             schedule_id: ID of the schedule entry
            
#         Returns:
#             Boolean indicating success
#         """
#         try:
#             # Validate input
#             if not isinstance(schedule_id, int) or schedule_id <= 0:
#                 logger.error(f"Invalid schedule ID: {schedule_id}")
#                 return False
            
#             # Update scheduled_posts table
#             cursor = self.conn.cursor()
#             cursor.execute(
#                 """
#                 UPDATE scheduled_posts
#                 SET status = 'Cancelled'
#                 WHERE id = ? AND status = 'Scheduled'
#                 """,
#                 (schedule_id,)
#             )
            
#             self.conn.commit()
            
#             if cursor.rowcount == 0:
#                 logger.warning(f"No active schedule with ID {schedule_id} found")
#                 return False
            
#             logger.info(f"Schedule {schedule_id} cancelled")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error cancelling post: {e}")
#             return False
    
#     def get_scheduled_posts(self, include_published=True, include_cancelled=False):
#         """Get list of scheduled posts.
        
#         Args:
#             include_published: Whether to include already published posts
#             include_cancelled: Whether to include cancelled posts
            
#         Returns:
#             List of scheduled post dictionaries
#         """
#         try:
#             cursor = self.conn.cursor()
            
#             # Build the SQL query based on parameters
#             status_conditions = ["'Scheduled'"]
#             if include_published:
#                 status_conditions.append("'Published'")
#             if include_cancelled:
#                 status_conditions.append("'Cancelled'")
            
#             status_clause = " OR ".join([f"sp.status = {status}" for status in status_conditions])
            
#             query = f"""
#                 SELECT sp.id, sp.post_id, gp.content, gp.hashtags, sp.scheduled_time, gp.profile, sp.status
#                 FROM scheduled_posts sp
#                 JOIN generated_posts gp ON sp.post_id = gp.id
#                 WHERE {status_clause}
#                 ORDER BY sp.scheduled_time DESC
#             """
            
#             cursor.execute(query)
            
#             scheduled_posts = []
#             for row in cursor.fetchall():
#                 scheduled_posts.append({
#                     "id": row[0],
#                     "post_id": row[1],
#                     "content": row[2],
#                     "hashtags": row[3],
#                     "scheduled_time": row[4],
#                     "profile": row[5],
#                     "status": row[6]
#                 })
            
#             return scheduled_posts
            
#         except Exception as e:
#             logger.error(f"Error retrieving scheduled posts: {e}")
#             return []
    
#     def _check_and_publish_due_posts(self):
#         """Check for due posts and mark them as published."""
#         try:
#             cursor = self.conn.cursor()
#             current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
#             # Get posts due for publishing
#             cursor.execute(
#                 """
#                 SELECT sp.id, sp.post_id, gp.content, gp.hashtags, gp.profile
#                 FROM scheduled_posts sp
#                 JOIN generated_posts gp ON sp.post_id = gp.id
#                 WHERE sp.status = 'Scheduled' AND sp.scheduled_time <= ?
#                 """,
#                 (current_time,)
#             )
            
#             due_posts = cursor.fetchall()
            
#             for post in due_posts:
#                 schedule_id, post_id, content, hashtags, profile = post
                
#                 # In a real implementation, this would call an API to post to LinkedIn
#                 # For now, we'll just mark as published
#                 self._publish_post(schedule_id, post_id, content, hashtags, profile)
                
#                 # Update status to published
#                 cursor.execute(
#                     """
#                     UPDATE scheduled_posts
#                     SET status = 'Published'
#                     WHERE id = ?
#                     """,
#                     (schedule_id,)
#                 )
            
#             if due_posts:
#                 self.conn.commit()
#                 logger.info(f"Published {len(due_posts)} due posts")
            
#         except Exception as e:
#             logger.error(f"Error checking for due posts: {e}")
    
#     def _publish_post(self, schedule_id, post_id, content, hashtags, profile):
#         """Publish post to LinkedIn (simulated).
        
#         In a real implementation, this would use the LinkedIn API.
#         """
#         try:
#             # Log the publishing action
#             full_content = content
#             if hashtags:
#                 full_content += "\n\n" + hashtags
                
#             logger.info(f"SIMULATED PUBLISHING for schedule {schedule_id}, post {post_id}")
#             logger.info(f"Profile: {profile}")
#             logger.info(f"Content: {full_content[:100]}...")
            
#             # In a real implementation, API call would go here
#             # Example:
#             # self._send_to_linkedin_api(profile, full_content)
            
#             return True
            
#         except Exception as e:
#             logger.error(f"Error publishing post {post_id}: {e}")
#             return False
    
#     def _send_to_linkedin_api(self, profile, content):
#         """Send post to LinkedIn API (placeholder).
        
#         This is a placeholder for the actual LinkedIn API implementation.
#         In a real application, you would:
#         1. Load API credentials for the profile
#         2. Use the LinkedIn API SDK or make REST calls
#         3. Handle rate limiting and errors
#         """
#         # Placeholder for LinkedIn API integration
#         # This would be implemented based on the LinkedIn API documentation
#         pass
    
#     def _scheduler_loop(self):
#         """Background thread for checking and publishing due posts."""
#         logger.info("Scheduler background thread started")
        
#         while True:
#             try:
#                 # Check for due posts
#                 self._check_and_publish_due_posts()
                
#                 # Sleep for a minute before checking again
#                 time.sleep(60)
                
#             except Exception as e:
#                 logger.error(f"Error in scheduler loop: {e}")
#                 time.sleep(60)  # Sleep and retry even after errors
    
#     def _start_scheduler_thread(self):
#         """Start the background scheduler thread."""
#         scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
#         scheduler_thread.start()
#         logger.info("Scheduler thread started")
    
#     def close(self):
#         """Close database connection."""
#         if self.conn:
#             self.conn.close()
import logging
from datetime import datetime
from src.utils import get_db_connection, schedule_post

logger = logging.getLogger(__name__)

class PostScheduler:
    def __init__(self):
        """Initialize the post scheduler."""
        self.conn = get_db_connection()
    
    def schedule_post(self, post_id, scheduled_time):
        """Schedule a post for publishing.
        
        Args:
            post_id: ID of the post to schedule
            scheduled_time: Datetime for scheduled publishing
            
        Returns:
            Boolean indicating success
        """
        try:
            schedule_post(post_id, scheduled_time.strftime("%Y-%m-%d %H:%M:%S"))
            return True
        except Exception as e:
            logger.error(f"Error scheduling post: {e}")
            return False
    
    def get_scheduled_posts(self):
        """Get all scheduled posts.
        
        Returns:
            List of scheduled post dictionaries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    id, 
                    content, 
                    hashtags, 
                    generated_at, 
                    scheduled_time,
                    published
                FROM generated_posts 
                WHERE scheduled_time IS NOT NULL
                ORDER BY scheduled_time ASC
            """)
            
            posts = []
            for row in cursor.fetchall():
                status = "Published" if row[5] == 1 else "Scheduled"
                posts.append({
                    "id": row[0],
                    "content": row[1],
                    "hashtags": row[2],
                    "generated_at": row[3],
                    "scheduled_time": row[4],
                    "status": status
                })
            
            return posts
        except Exception as e:
            logger.error(f"Error getting scheduled posts: {e}")
            return []
    
    def reschedule_post(self, post_id, new_time):
        """Reschedule a post.
        
        Args:
            post_id: ID of the post to reschedule
            new_time: New datetime for scheduled publishing
            
        Returns:
            Boolean indicating success
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE generated_posts SET scheduled_time = ? WHERE id = ? AND published = 0",
                (new_time.strftime("%Y-%m-%d %H:%M:%S"), post_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error rescheduling post: {e}")
            return False
    
    def cancel_post(self, post_id):
        """Cancel a scheduled post.
        
        Args:
            post_id: ID of the post to cancel
            
        Returns:
            Boolean indicating success
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE generated_posts SET scheduled_time = NULL WHERE id = ? AND published = 0",
                (post_id,)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error canceling post: {e}")
            return False
    
    def mark_as_published(self, post_id):
        """Mark a post as published.
        
        Args:
            post_id: ID of the post to mark as published
            
        Returns:
            Boolean indicating success
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE generated_posts SET published = 1 WHERE id = ?",
                (post_id,)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error marking post as published: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()