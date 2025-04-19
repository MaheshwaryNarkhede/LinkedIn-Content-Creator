import logging
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

from src.utils import get_db_connection

logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, headless=True, login_email=None, login_password=None):
        """Initialize the LinkedIn scraper.
        
        Args:
            headless: Whether to run browser in headless mode
            login_email: LinkedIn login email (optional)
            login_password: LinkedIn login password (optional)
        """
        self.headless = headless
        self.login_email = login_email
        self.login_password = login_password
        self.driver = None
        
    def _initialize_driver(self):
        """Initialize and configure the Selenium WebDriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def login(self):
        """Login to LinkedIn with provided credentials."""
        if not self.login_email or not self.login_password:
            logger.warning("LinkedIn credentials not provided. Some content may not be accessible.")
            return False
            
        if not self.driver:
            self._initialize_driver()
            
        self.driver.get("https://www.linkedin.com/login")
        
        try:
            # Input email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.send_keys(self.login_email)
            
            # Input password
            password_input = self.driver.find_element(By.ID, "password")
            password_input.send_keys(self.login_password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("linkedin.com/feed")
            )
            
            logger.info("Successfully logged in to LinkedIn")
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def scrape_profile_posts(self, profile_url, profile_name, max_posts=20):
        """Scrape posts from a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL
            profile_name: Name of the profile owner
            max_posts: Maximum number of posts to scrape
            
        Returns:
            List of dictionaries containing post data
        """
        if not self.driver:
            self._initialize_driver()
            
        posts_url = f"{profile_url.rstrip('/')}/recent-activity/shares/"
        self.driver.get(posts_url)
        logger.info(f"Accessing posts for profile: {profile_name} at {posts_url}")
        
        # Wait for posts to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'feed-shared-update-v2')]"))
            )
        except TimeoutException:
            logger.warning(f"No posts found for profile: {profile_name}")
            return []
        
        # Scroll to load more posts
        posts_found = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while posts_found < max_posts:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for page to load
            time.sleep(random.uniform(2, 4))
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            posts_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'feed-shared-update-v2')]")
            posts_found = len(posts_elements)
            
            logger.info(f"Found {posts_found} posts so far...")
            
            if new_height == last_height or posts_found >= max_posts:
                break
                
            last_height = new_height
        
        # Extract post data
        posts_data = []
        posts_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'feed-shared-update-v2')]")
        
        for i, post_element in enumerate(posts_elements[:max_posts]):
            try:
                # Get post URL
                post_url_element = post_element.find_element(By.XPATH, ".//a[contains(@class, 'app-aware-link') and contains(@href, '/posts/')]")
                post_url = post_url_element.get_attribute("href")
                
                # Get post content
                try:
                    post_content_element = post_element.find_element(By.XPATH, ".//div[contains(@class, 'feed-shared-update-v2__description')]")
                    post_content = post_content_element.text
                except NoSuchElementException:
                    post_content = ""
                
                # Get engagement metrics
                try:
                    likes_element = post_element.find_element(By.XPATH, ".//span[contains(@class, 'social-details-social-counts__reactions-count')]")
                    likes = self._parse_count(likes_element.text)
                except NoSuchElementException:
                    likes = 0
                    
                try:
                    comments_element = post_element.find_element(By.XPATH, ".//li[contains(@class, 'social-details-social-counts__comments')]")
                    comments = self._parse_count(comments_element.text)
                except NoSuchElementException:
                    comments = 0
                    
                try:
                    shares_element = post_element.find_element(By.XPATH, ".//li[contains(@class, 'social-details-social-counts__reshares')]")
                    shares = self._parse_count(shares_element.text)
                except NoSuchElementException:
                    shares = 0
                
                # Get publish date (approximate from URL or post element)
                publish_date = datetime.now().strftime("%Y-%m-%d")  # Default to today if can't extract
                
                post_data = {
                    "profile_url": profile_url,
                    "profile_name": profile_name,
                    "post_url": post_url,
                    "post_content": post_content,
                    "publish_date": publish_date,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "collected_at": datetime.now().isoformat()
                }
                
                posts_data.append(post_data)
                logger.info(f"Scraped post {i+1}/{min(max_posts, len(posts_elements))}")
                
            except Exception as e:
                logger.error(f"Error scraping post {i+1}: {str(e)}")
        
        return posts_data
    
    def _parse_count(self, count_text):
        """Parse engagement count from text."""
        if not count_text:
            return 0
            
        count_text = count_text.replace(',', '').strip()
        
        if 'K' in count_text:
            return int(float(count_text.replace('K', '')) * 1000)
        elif 'M' in count_text:
            return int(float(count_text.replace('M', '')) * 1000000)
        elif count_text.isdigit():
            return int(count_text)
        else:
            return 0
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

def save_posts_to_database(posts_data):
    """Save scraped posts to the database.
    
    Args:
        posts_data: List of dictionaries containing post data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for post in posts_data:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO posts 
                (profile_url, profile_name, post_url, post_content, publish_date, likes, comments, shares, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post["profile_url"],
                    post["profile_name"],
                    post["post_url"],
                    post["post_content"],
                    post["publish_date"],
                    post["likes"],
                    post["comments"],
                    post["shares"],
                    post["collected_at"]
                )
            )
        except Exception as e:
            logger.error(f"Error saving post to database: {str(e)}")
    
    conn.commit()
    conn.close()
    logger.info(f"Saved {len(posts_data)} posts to database")

def scrape_linkedin_profiles(profiles_config, max_posts_per_profile=20):
    """Scrape posts from LinkedIn profiles specified in config.
    
    Args:
        profiles_config: Dictionary containing profile information
        max_posts_per_profile: Maximum number of posts to scrape per profile
    """
    if not profiles_config:
        logger.error("No profiles configuration provided")
        return
    
    # Initialize and use scraper
    scraper = LinkedInScraper(headless=True)
    
    try:
        # Scrape target profile
        target_profile = profiles_config.get("target_profile")
        if target_profile:
            logger.info(f"Scraping target profile: {target_profile['name']}")
            target_posts = scraper.scrape_profile_posts(
                target_profile["url"], 
                target_profile["name"],
                max_posts=max_posts_per_profile
            )
            save_posts_to_database(target_posts)
        
        # Scrape competitor profiles
        competitor_profiles = profiles_config.get("competitor_profiles", [])
        for profile in competitor_profiles:
            logger.info(f"Scraping competitor profile: {profile['name']}")
            competitor_posts = scraper.scrape_profile_posts(
                profile["url"], 
                profile["name"],
                max_posts=max_posts_per_profile
            )
            save_posts_to_database(competitor_posts)
            
            # Add delay between profiles to avoid rate limiting
            time.sleep(random.uniform(5, 10))
    
    finally:
        scraper.close()

def fetch_posts_from_database(profile_name=None, limit=50):
    """Fetch posts from database with optional filter by profile.
    
    Args:
        profile_name: Optional filter by profile name
        limit: Maximum number of posts to fetch
        
    Returns:
        List of post dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if profile_name:
        cursor.execute(
            "SELECT * FROM posts WHERE profile_name = ? ORDER BY likes + comments + shares DESC LIMIT ?",
            (profile_name, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM posts ORDER BY likes + comments + shares DESC LIMIT ?",
            (limit,)
        )
    
    columns = [description[0] for description in cursor.description]
    posts = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return posts