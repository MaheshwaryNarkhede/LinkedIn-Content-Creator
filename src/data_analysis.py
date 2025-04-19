import logging
import pandas as pd
import numpy as np
from datetime import datetime
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import emoji

from src.utils import get_db_connection

logger = logging.getLogger(__name__)

# Download NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK resources: {e}")

class LinkedInPostAnalyzer:
    def __init__(self):
        """Initialize the LinkedIn post analyzer."""
        self.conn = get_db_connection()
        self.posts_df = None
        self.load_data()
        
    def load_data(self):
        """Load posts data from database into DataFrame."""
        query = "SELECT * FROM posts"
        self.posts_df = pd.read_sql_query(query, self.conn)
        
        # Convert date columns to datetime
        for date_col in ['publish_date', 'collected_at']:
            try:
                self.posts_df[date_col] = pd.to_datetime(self.posts_df[date_col])
            except Exception as e:
                logger.warning(f"Failed to convert {date_col} to datetime: {e}")
                
        logger.info(f"Loaded {len(self.posts_df)} posts for analysis")
        
    def calculate_engagement_metrics(self):
        """Calculate engagement metrics for posts."""
        if self.posts_df is None or self.posts_df.empty:
            logger.warning("No posts data available for analysis")
            return {}
            
        # Calculate total engagement
        self.posts_df['total_engagement'] = self.posts_df['likes'] + self.posts_df['comments'] + self.posts_df['shares']
        
        # Calculate engagement rate metrics
        engagement_metrics = {
            'avg_likes': self.posts_df['likes'].mean(),
            'median_likes': self.posts_df['likes'].median(),
            'avg_comments': self.posts_df['comments'].mean(),
            'median_comments': self.posts_df['comments'].median(),
            'avg_shares': self.posts_df['shares'].mean(),
            'median_shares': self.posts_df['shares'].median(),
            'avg_total_engagement': self.posts_df['total_engagement'].mean(),
            'median_total_engagement': self.posts_df['total_engagement'].median(),
        }
        
        # Calculate by profile
        profile_metrics = self.posts_df.groupby('profile_name').agg({
            'likes': ['mean', 'median', 'max'],
            'comments': ['mean', 'median', 'max'],
            'shares': ['mean', 'median', 'max'],
            'total_engagement': ['mean', 'median', 'max']
        }).reset_index()
        
        return {
            'overall': engagement_metrics,
            'by_profile': profile_metrics.to_dict()
        }
    
    def analyze_post_timing(self):
        """Analyze post timing patterns."""
        if self.posts_df is None or self.posts_df.empty:
            logger.warning("No posts data available for timing analysis")
            return {}
            
        try:
            # Extract hour of day and day of week
            self.posts_df['hour_of_day'] = self.posts_df['publish_date'].dt.hour
            self.posts_df['day_of_week'] = self.posts_df['publish_date'].dt.dayofweek
            
            # Get average engagement by hour and day
            hour_engagement = self.posts_df.groupby('hour_of_day')['total_engagement'].mean().reset_index()
            day_engagement = self.posts_df.groupby('day_of_week')['total_engagement'].mean().reset_index()
            
            # Find optimal posting times
            best_hours = hour_engagement.sort_values('total_engagement', ascending=False)['hour_of_day'].tolist()
            best_days = day_engagement.sort_values('total_engagement', ascending=False)['day_of_week'].tolist()
            
            return {
                'best_hours': best_hours[:3],  # Top 3 hours
                'best_days': best_days[:3],    # Top 3 days
                'hour_engagement': hour_engagement.to_dict(),
                'day_engagement': day_engagement.to_dict()
            }
        except Exception as e:
            logger.error(f"Error analyzing post timing: {e}")
            return {}
    
    def extract_topics_and_keywords(self):
        """Extract common topics and keywords from posts."""
        if self.posts_df is None or self.posts_df.empty or 'post_content' not in self.posts_df.columns:
            logger.warning("No post content available for topic extraction")
            return {}
            
        try:
            # Combine all post content
            all_content = ' '.join(self.posts_df['post_content'].fillna(''))
            
            # Tokenize and remove stopwords
            stop_words = set(stopwords.words('english'))
            word_tokens = word_tokenize(all_content.lower())
            filtered_tokens = [w for w in word_tokens if w.isalpha() and w not in stop_words and len(w) > 2]
            
            # Get most common words
            word_freq = Counter(filtered_tokens)
            common_words = word_freq.most_common(20)
            
            # Get most common bigrams
            bi_grams = list(ngrams(filtered_tokens, 2))
            bigram_freq = Counter(bi_grams)
            common_bigrams = [(f"{bg[0]} {bg[1]}", count) for bg, count in bigram_freq.most_common(15)]
            
            # Extract hashtags
            hashtag_pattern = r'#(\w+)'
            all_hashtags = []
            
            for content in self.posts_df['post_content'].fillna(''):
                hashtags = re.findall(hashtag_pattern, content)
                all_hashtags.extend([tag.lower() for tag in hashtags])
            
            hashtag_freq = Counter(all_hashtags)
            common_hashtags = hashtag_freq.most_common(15)
            
            # Try clustering posts by content
            tfidf_vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                min_df=2
            )
            
            # Filter out empty content
            valid_posts = self.posts_df[self.posts_df['post_content'].notna() & (self.posts_df['post_content'] != '')]
            
            if len(valid_posts) >= 5:  # Need minimum posts for meaningful clustering
                tfidf_matrix = tfidf_vectorizer.fit_transform(valid_posts['post_content'])
                
                # Determine optimal number of clusters (2-5)
                num_clusters = min(5, len(valid_posts) // 2)
                kmeans = KMeans(n_clusters=num_clusters, random_state=42)
                kmeans.fit(tfidf_matrix)
                
                # Get top terms per cluster
                order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
                terms = tfidf_vectorizer.get_feature_names_out()
                
                topics = []
                for i in range(num_clusters):
                    topic_terms = [terms[idx] for idx in order_centroids[i, :10]]
                    topics.append({
                        'id': i,
                        'terms': topic_terms,
                        'size': np.sum(kmeans.labels_ == i)
                    })
            else:
                topics = []
            
            return {
                'common_words': common_words,
                'common_bigrams': common_bigrams,
                'common_hashtags': common_hashtags,
                'topics': topics
            }
        except Exception as e:
            logger.error(f"Error extracting topics and keywords: {e}")
            return {}
    
    def analyze_post_structure(self):
        """Analyze the structure of successful posts."""
        if self.posts_df is None or self.posts_df.empty:
            logger.warning("No posts data available for structure analysis")
            return {}
            
        try:
            # Add length metrics
            self.posts_df['content_length'] = self.posts_df['post_content'].fillna('').apply(len)
            self.posts_df['word_count'] = self.posts_df['post_content'].fillna('').apply(lambda x: len(x.split()))
            self.posts_df['has_hashtags'] = self.posts_df['post_content'].fillna('').str.contains(r'#\w+')
            self.posts_df['hashtag_count'] = self.posts_df['post_content'].fillna('').apply(
                lambda x: len(re.findall(r'#\w+', x))
            )
            self.posts_df['has_url'] = self.posts_df['post_content'].fillna('').str.contains(r'https?://\S+')
            self.posts_df['has_mention'] = self.posts_df['post_content'].fillna('').str.contains(r'@\w+')
            self.posts_df['has_emoji'] = self.posts_df['post_content'].fillna('').apply(
                lambda x: any(c in emoji.EMOJI_DATA for c in x)
            )
            self.posts_df['has_question'] = self.posts_df['post_content'].fillna('').str.contains(r'\?')
            self.posts_df['sentence_count'] = self.posts_df['post_content'].fillna('').apply(
                lambda x: len(re.split(r'[.!?]+', x))
            )
            
            # Segment posts by engagement
            high_engagement = self.posts_df[self.posts_df['total_engagement'] > self.posts_df['total_engagement'].median()]
            
            # Calculate structure metrics for high engagement posts
            structure_metrics = {
                'avg_content_length': high_engagement['content_length'].mean(),
                'avg_word_count': high_engagement['word_count'].mean(),
                'avg_hashtag_count': high_engagement['hashtag_count'].mean(),
                'pct_with_hashtags': high_engagement['has_hashtags'].mean() * 100,
                'pct_with_url': high_engagement['has_url'].mean() * 100,
                'pct_with_mention': high_engagement['has_mention'].mean() * 100,
                'pct_with_emoji': high_engagement['has_emoji'].mean() * 100,
                'pct_with_question': high_engagement['has_question'].mean() * 100,
                'avg_sentence_count': high_engagement['sentence_count'].mean()
            }
            
            # Find correlation between structure and engagement
            structure_cols = [
                'content_length', 'word_count', 'hashtag_count', 'has_hashtags', 
                'has_url', 'has_mention', 'has_emoji', 'has_question', 'sentence_count'
            ]
            
            correlations = {}
            for col in structure_cols:
                correlations[col] = self.posts_df[[col, 'total_engagement']].corr().iloc[0, 1]
            
            return {
                'structure_metrics': structure_metrics,
                'correlations': correlations
            }
        except Exception as e:
            logger.error(f"Error analyzing post structure: {e}")
            return {}
    
    def identify_top_performing_posts(self, limit=5):
        """Identify top performing posts and extract patterns."""
        if self.posts_df is None or self.posts_df.empty:
            logger.warning("No posts data available for top performers analysis")
            return []
            
        try:
            # Sort by total engagement
            self.posts_df['total_engagement'] = self.posts_df['likes'] + self.posts_df['comments'] + self.posts_df['shares']
            top_posts = self.posts_df.sort_values('total_engagement', ascending=False).head(limit)
            
            # Extract key patterns from top posts
            top_posts_patterns = []
            
            for _, post in top_posts.iterrows():
                patterns = {
                    'post_id': post['id'],
                    'profile_name': post['profile_name'],
                    'content': post['post_content'],
                    'likes': post['likes'],
                    'comments': post['comments'],
                    'shares': post['shares'],
                    'total_engagement': post['total_engagement'],
                    'word_count': len(post['post_content'].split()) if post['post_content'] else 0,
                    'hashtags': re.findall(r'#(\w+)', post['post_content']) if post['post_content'] else [],
                    'has_url': bool(re.search(r'https?://\S+', post['post_content'])) if post['post_content'] else False,
                    'has_mention': bool(re.search(r'@\w+', post['post_content'])) if post['post_content'] else False,
                    'has_question': '?' in post['post_content'] if post['post_content'] else False
                }
                top_posts_patterns.append(patterns)
            
            return top_posts_patterns
        except Exception as e:
            logger.error(f"Error identifying top performing posts: {e}")
            return []
    
    def generate_recommendations(self):
        """Generate content recommendations based on analysis."""
        recommendations = {}
        
        # Structure recommendations
        structure_analysis = self.analyze_post_structure()
        structure_metrics = structure_analysis.get('structure_metrics', {})
        correlations = structure_analysis.get('correlations', {})
        
        structure_recommendations = []
        
        # Word count recommendation
        if structure_metrics.get('avg_word_count'):
            structure_recommendations.append(
                f"Aim for around {int(structure_metrics['avg_word_count'])} words per post"
            )
        
        # Hashtag recommendation
        if structure_metrics.get('avg_hashtag_count'):
            structure_recommendations.append(
                f"Use approximately {int(structure_metrics['avg_hashtag_count'])} hashtags per post"
            )
        
        # Include emoji recommendation
        if structure_metrics.get('pct_with_emoji', 0) > 50:
            structure_recommendations.append(
                "Include emojis in your posts for better engagement"
            )
        
        # Questions recommendation
        if correlations.get('has_question', 0) > 0.2:
            structure_recommendations.append(
                "Including questions in posts tends to increase engagement"
            )
        
        # URL recommendation
        if correlations.get('has_url', 0) > 0.2:
            structure_recommendations.append(
                "Including links in posts correlates with higher engagement"
            )
        
        recommendations['structure'] = structure_recommendations
        
        # Topic recommendations
        topic_analysis = self.extract_topics_and_keywords()
        
        topic_recommendations = []
        
        # Keyword recommendations
        common_words = topic_analysis.get('common_words', [])
        if common_words:
            top_keywords = [word for word, _ in common_words[:10]]
            topic_recommendations.append(
                f"Focus on these key topics: {', '.join(top_keywords)}"
            )
        
        # Hashtag recommendations
        common_hashtags = topic_analysis.get('common_hashtags', [])
        if common_hashtags:
            top_hashtags = [f"#{tag}" for tag, _ in common_hashtags[:5]]
            topic_recommendations.append(
                f"Consider using these popular hashtags: {', '.join(top_hashtags)}"
            )
        
        recommendations['topics'] = topic_recommendations
        
        # Timing recommendations
        timing_analysis = self.analyze_post_timing()
        
        timing_recommendations = []
        
        # Best hours recommendation
        best_hours = timing_analysis.get('best_hours', [])
        if best_hours:
            timing_recommendations.append(
                f"Post at these hours for maximum engagement: {', '.join(map(str, best_hours))}"
            )
        
        # Best days recommendation
        best_days = timing_analysis.get('best_days', [])
        if best_days:
            days_map = {
                0: 'Monday',
                1: 'Tuesday',
                2: 'Wednesday',
                3: 'Thursday',
                4: 'Friday',
                5: 'Saturday',
                6: 'Sunday'
            }
            best_days_names = [days_map.get(day, str(day)) for day in best_days]
            timing_recommendations.append(
                f"Best days to post: {', '.join(best_days_names)}"
            )
        
        recommendations['timing'] = timing_recommendations
        
        return recommendations
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()