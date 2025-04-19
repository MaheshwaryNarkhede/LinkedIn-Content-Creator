# import logging
# import json
# import sqlite3
# from datetime import datetime

# from src.utils import get_db_connection, update_post_feedback

# logger = logging.getLogger(__name__)

# class FeedbackHandler:
#     def __init__(self):
#         """Initialize the feedback handler."""
#         self.conn = get_db_connection()
        
#     def record_feedback(self, post_id, feedback_score, feedback_text):
#         """Record user feedback for a generated post.
        
#         Args:
#             post_id: ID of the generated post
#             feedback_score: Numerical score (1-5)
#             feedback_text: Text feedback
            
#         Returns:
#             Success status boolean
#         """
#         try:
#             # Validate inputs
#             if not isinstance(post_id, int) or post_id <= 0:
#                 logger.error(f"Invalid post ID: {post_id}")
#                 return False
                
#             if not isinstance(feedback_score, int) or feedback_score < 1 or feedback_score > 5:
#                 logger.error(f"Invalid feedback score: {feedback_score}. Must be between 1-5.")
#                 return False
            
#             # Update post with feedback
#             update_post_feedback(post_id, feedback_score, feedback_text)
            
#             logger.info(f"Recorded feedback for post {post_id}: Score={feedback_score}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error recording feedback: {e}")
#             return False
    
#     def get_feedback_history(self, limit=10):
#         """Get history of feedback provided.
        
#         Args:
#             limit: Maximum number of feedback entries to return
            
#         Returns:
#             List of feedback dictionaries
#         """
#         try:
#             cursor = self.conn.cursor()
#             cursor.execute(
            
#             """
#                 SELECT id, content, hashtags, generated_at, feedback_score, feedback_text 
#                 FROM generated_posts 
#                 WHERE feedback_score IS NOT NULL 
#                 ORDER BY generated_at DESC 
#                 LIMIT ?
#                 """,
#                 (limit,)
#             )
            
#             feedback_history = []
#             for row in cursor.fetchall():
#                 feedback_history.append({
#                     "id": row[0],
#                     "content": row[1],
#                     "hashtags": row[2],
#                     "generated_at": row[3],
#                     "feedback_score": row[4],
#                     "feedback_text": row[5]
#                 })
            
#             return feedback_history
            
#         except Exception as e:
#             logger.error(f"Error retrieving feedback history: {e}")
#             return []
    
#     def get_average_feedback_score(self):
#         """Get the average feedback score across all posts.
        
#         Returns:
#             Float representing average score or None if no feedback exists
#         """
#         try:
#             cursor = self.conn.cursor()
#             cursor.execute(
#                 """
#                 SELECT AVG(feedback_score) 
#                 FROM generated_posts 
#                 WHERE feedback_score IS NOT NULL
#                 """
#             )
            
#             avg_score = cursor.fetchone()[0]
#             return avg_score
            
#         except Exception as e:
#             logger.error(f"Error calculating average feedback score: {e}")
#             return None
    
#     def get_feedback_summary(self):
#         """Get a summary of feedback statistics.
        
#         Returns:
#             Dictionary with feedback statistics
#         """
#         try:
#             cursor = self.conn.cursor()
            
#             # Get count by score
#             cursor.execute(
#                 """
#                 SELECT feedback_score, COUNT(*) 
#                 FROM generated_posts 
#                 WHERE feedback_score IS NOT NULL 
#                 GROUP BY feedback_score
#                 """
#             )
            
#             score_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
#             for row in cursor.fetchall():
#                 score_distribution[row[0]] = row[1]
            
#             # Get total feedback count
#             cursor.execute(
#                 """
#                 SELECT COUNT(*) 
#                 FROM generated_posts 
#                 WHERE feedback_score IS NOT NULL
#                 """
#             )
#             total_feedback = cursor.fetchone()[0]
            
#             # Get average score
#             avg_score = self.get_average_feedback_score()
            
#             return {
#                 "total_feedback": total_feedback,
#                 "average_score": avg_score,
#                 "score_distribution": score_distribution
#             }
            
#         except Exception as e:
#             logger.error(f"Error generating feedback summary: {e}")
#             return {
#                 "total_feedback": 0,
#                 "average_score": None,
#                 "score_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
#             }
    
#     def close(self):
#         """Close database connection."""
#         if self.conn:
#             self.conn.close()
import logging
from datetime import datetime
from src.utils import get_db_connection, update_post_feedback

logger = logging.getLogger(__name__)

class FeedbackHandler:
    def __init__(self):
        """Initialize the feedback handler."""
        self.conn = get_db_connection()
        
    def record_feedback(self, post_id, feedback_score, feedback_text):
        """Record feedback for a generated post.
        
        Args:
            post_id: ID of the post to update
            feedback_score: Score from 1-5
            feedback_text: Text feedback
            
        Returns:
            Boolean indicating success
        """
        try:
            update_post_feedback(post_id, feedback_score, feedback_text)
            return True
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False
    
    def get_feedback_summary(self):
        """Get a summary of feedback statistics.
        
        Returns:
            Dictionary with feedback summary
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(feedback_score) as average,
                    feedback_score
                FROM generated_posts 
                WHERE feedback_score IS NOT NULL
                GROUP BY feedback_score
                ORDER BY feedback_score ASC
            """)
            
            summary = {
                "total_feedback": 0,
                "average_score": 0,
                "score_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
            
            rows = cursor.fetchall()
            if rows:
                # Calculate total and populate score distribution
                total = 0
                weighted_sum = 0
                
                for row in rows:
                    count = row[0]
                    score = row[2]
                    total += count
                    weighted_sum += score * count
                    summary["score_distribution"][score] = count
                
                summary["total_feedback"] = total
                summary["average_score"] = weighted_sum / total if total > 0 else 0
            
            return summary
        except Exception as e:
            logger.error(f"Error getting feedback summary: {e}")
            return {
                "total_feedback": 0,
                "average_score": 0,
                "score_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
    
    def get_feedback_history(self, limit=10):
        """Get recent feedback history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of feedback records
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    id, 
                    content, 
                    hashtags, 
                    generated_at, 
                    feedback_score, 
                    feedback_text
                FROM generated_posts 
                WHERE feedback_score IS NOT NULL
                ORDER BY generated_at DESC
                LIMIT ?
            """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row[0],
                    "content": row[1],
                    "hashtags": row[2],
                    "generated_at": row[3],
                    "feedback_score": row[4],
                    "feedback_text": row[5]
                })
            
            return history
        except Exception as e:
            logger.error(f"Error getting feedback history: {e}")
            return []
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()