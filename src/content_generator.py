# import logging
# import os
# import json
# import random
# import re
# import time
# from datetime import datetime
# import openai
# from anthropic import Anthropic
# import numpy as np
# from dotenv import load_dotenv

# from src.utils import get_db_connection, save_generated_post
# from src.data_analysis import LinkedInPostAnalyzer

# # Load environment variables
# load_dotenv()

# logger = logging.getLogger(__name__)

# class PostGenerator:
#     def __init__(self, ai_provider="openai"):
#         """Initialize the content generator.
        
#         Args:
#             ai_provider: AI provider to use ('openai' or 'anthropic')
#         """
#         self.ai_provider = ai_provider
#         self.analyzer = LinkedInPostAnalyzer()
        
#         # Initialize AI clients
#         if ai_provider == "openai":
#             self.setup_openai()
#         elif ai_provider == "anthropic":
#             self.setup_anthropic()
#         else:
#             logger.warning(f"Unknown AI provider: {ai_provider}. Defaulting to OpenAI.")
#             self.ai_provider = "openai"
#             self.setup_openai()
            
#         # Get content recommendations from analyzer
#         self.recommendations = self.analyzer.generate_recommendations()
        
#         # Get top performing posts for reference
#         self.top_posts = self.analyzer.identify_top_performing_posts(limit=3)
        
#     def setup_openai(self):
#         """Setup OpenAI API client."""
#         openai_api_key = os.getenv("OPENAI_API_KEY")
#         if not openai_api_key:
#             logger.warning("OpenAI API key not found in environment variables.")
        
#         openai.api_key = openai_api_key
        
#     def setup_anthropic(self):
#         """Setup Anthropic API client."""
#         anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
#         if not anthropic_api_key:
#             logger.warning("Anthropic API key not found in environment variables.")
            
#         self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        
#     def generate_post_prompt(self, topic=None, tone=None, target_audience=None, custom_instructions=None):
#         """Generate a prompt for AI to create LinkedIn posts.
        
#         Args:
#             topic: Optional topic for the post
#             tone: Optional tone for the post
#             target_audience: Optional target audience for the post
#             custom_instructions: Optional custom instructions
            
#         Returns:
#             Formatted prompt string
#         """
#         # Start with base prompt
#         prompt = "Generate a LinkedIn post "
        
#         # Add topic if provided
#         if topic:
#             prompt += f"about {topic} "
        
#         # Add tone if provided
#         if tone:
#             prompt += f"in a {tone} tone "
        
#         # Add target audience if provided
#         if target_audience:
#             prompt += f"targeted at {target_audience} "
        
#         # Add custom instructions if provided
#         if custom_instructions:
#             prompt += f"with the following requirements: {custom_instructions} "
        
#         # Add recommendations based on analysis
#         prompt += "\n\nBased on analysis of successful LinkedIn posts, please follow these guidelines:\n"
        
#         # Add structure recommendations
#         structure_recommendations = self.recommendations.get('structure', [])
#         if structure_recommendations:
#             prompt += "\nStructure guidelines:\n"
#             for rec in structure_recommendations:
#                 prompt += f"- {rec}\n"
        
#         # Add topic recommendations
#         topic_recommendations = self.recommendations.get('topics', [])
#         if topic_recommendations:
#             prompt += "\nTopic guidelines:\n"
#             for rec in topic_recommendations:
#                 prompt += f"- {rec}\n"
        
#         # Add examples of successful posts
#         if self.top_posts:
#             prompt += "\nHere are examples of successful posts for reference:\n"
#             for i, post in enumerate(self.top_posts, 1):
#                 content = post.get('content', '')
#                 if content:
#                     # Truncate long posts
#                     if len(content) > 300:
#                         content = content[:297] + "..."
#                     prompt += f"\nExample {i}:\n{content}\n"
        
#         # Add specific output format instructions
#         prompt += "\nPlease provide the post in two parts:\n1. The main content of the post\n2. A list of 3-5 relevant hashtags"
        
#         # Add variation instructions if generating multiple variations
#         prompt += "\n\nGenerate two different variations of this post that are distinct in approach but follow the same guidelines."
        
#         return prompt
        
#     def generate_posts(self, topic=None, tone=None, target_audience=None, custom_instructions=None, num_variants=2):
#         """Generate LinkedIn posts using AI.
        
#         Args:
#             topic: Optional topic for the post
#             tone: Optional tone for the post
#             target_audience: Optional target audience for the post
#             custom_instructions: Optional custom instructions
#             num_variants: Number of post variants to generate
            
#         Returns:
#             List of generated post dictionaries
#         """
#         prompt = self.generate_post_prompt(topic, tone, target_audience, custom_instructions)
        
#         try:
#             if self.ai_provider == "openai":
#                 return self._generate_with_openai(prompt, num_variants)
#             elif self.ai_provider == "anthropic":
#                 return self._generate_with_anthropic(prompt, num_variants)
#             else:
#                 logger.warning(f"Unknown AI provider: {self.ai_provider}")
#                 return []
#         except Exception as e:
#             logger.error(f"Error generating posts: {e}")
#             return []
    
#     def _generate_with_openai(self, prompt, num_variants):
#         """Generate posts using OpenAI API.
        
#         Args:
#             prompt: The prompt to send to OpenAI
#             num_variants: Number of variants to generate
            
#         Returns:
#             List of generated post dictionaries
#         """
#         try:
#             response = openai.ChatCompletion.create(
#                 model="gpt-4",
#                 messages=[
#                     {"role": "system", "content": "You are a professional LinkedIn content creator who specializes in creating engaging posts that drive high engagement."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.7,
#                 max_tokens=1000,
#                 n=1
#             )
            
#             content = response.choices[0].message.content
            
#             # Parse the response to extract post variants
#             return self._parse_generated_content(content, num_variants)
#         except Exception as e:
#             logger.error(f"OpenAI API error: {e}")
#             return []
    
#     def _generate_with_anthropic(self, prompt, num_variants):
#         """Generate posts using Anthropic API.
        
#         Args:
#             prompt: The prompt to send to Anthropic
#             num_variants: Number of variants to generate
            
#         Returns:
#             List of generated post dictionaries
#         """
#         try:
#             response = self.anthropic_client.messages.create(
#                 model="claude-3-haiku-20240307",
#                 max_tokens=1000,
#                 temperature=0.7,
#                 system="You are a professional LinkedIn content creator who specializes in creating engaging posts that drive high engagement.",
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ]
#             )
            
#             content = response.content[0].text
            
#             # Parse the response to extract post variants
#             return self._parse_generated_content(content, num_variants)
#         except Exception as e:
#             logger.error(f"Anthropic API error: {e}")
#             return []
    
#     def _parse_generated_content(self, content, num_variants):
#         """Parse the AI-generated content to extract post variants.
        
#         Args:
#             content: Text content from AI response
#             num_variants: Expected number of variants
            
#         Returns:
#             List of post dictionaries
#         """
#         posts = []
        
#         # Try to identify variations in the response
#         variations = []
        
#         # Pattern for variations labeled as "Variation X" or "Post X"
#         variation_patterns = [
#             r"(?:Variation|VARIATION|variation)\s*(\d+):(.*?)(?=(?:Variation|VARIATION|variation)\s*\d+:|$)",
#             r"(?:Post|POST|post)\s*(\d+):(.*?)(?=(?:Post|POST|post)\s*\d+:|$)",
#             r"(?:Version|VERSION|version)\s*(\d+):(.*?)(?=(?:Version|VERSION|version)\s*\d+:|$)",
#             r"(?:Option|OPTION|option)\s*(\d+):(.*?)(?=(?:Option|OPTION|option)\s*\d+:|$)"
#         ]
        
#         # Try each pattern until we find matches
#         for pattern in variation_patterns:
#             matches = re.findall(pattern, content, re.DOTALL)
#             if matches:
#                 for _, match_content in matches:
#                     variations.append(match_content.strip())
#                 break
        
#         # If no variations found, try splitting by numbered list markers
#         if not variations:
#             list_pattern = r"(?:^|\n)\s*(\d+)[.)]\s*(.*?)(?=(?:^|\n)\s*\d+[.)]\s*|$)"
#             matches = re.findall(list_pattern, content, re.DOTALL | re.MULTILINE)
#             if matches:
#                 for _, match_content in matches:
#                     variations.append(match_content.strip())
        
#         # If still no variations, treat the entire response as one post
#         if not variations:
#             variations = [content]
        
#         # Limit to requested number of variants
#         variations = variations[:num_variants]
        
#         # Process each variation to extract content and hashtags
#         for i, variation in enumerate(variations):
#             # Check for explicit "Hashtags:" section
#             content_parts = re.split(r"(?:Hashtags|HASHTAGS|hashtags):", variation, maxsplit=1)
            
#             if len(content_parts) > 1:
#                 post_content = content_parts[0].strip()
#                 hashtags_section = content_parts[1].strip()
                
#                 # Extract hashtags
#                 hashtags = re.findall(r'#\w+', hashtags_section)
#                 hashtags_str = ' '.join(hashtags)
                
#                 # Remove any hashtags already in the content if they're duplicated in the hashtags section
#                 for hashtag in hashtags:
#                     if hashtag in post_content:
#                         post_content = post_content.replace(hashtag, '')
                
#                 post_content = post_content.strip()
#             else:
#                 # If no explicit hashtags section, extract hashtags from the post content
#                 post_content = variation.strip()
#                 hashtags = re.findall(r'#\w+', post_content)
#                 hashtags_str = ' '.join(hashtags)
            
#             posts.append({
#                 'content': post_content,
#                 'hashtags': hashtags_str,
#                 'variant': i + 1
#             })
        
#         # If we still don't have enough variants, duplicate the last one
#         while len(posts) < num_variants:
#             if posts:
#                 last_post = posts[-1].copy()
#                 last_post['variant'] = len(posts) + 1
#                 posts.append(last_post)
#             else:
#                 # Emergency fallback
#                 posts.append({
#                     'content': "We were unable to generate a post with the given parameters. Please try again with different inputs.",
#                     'hashtags': "#linkedin #post",
#                     'variant': len(posts) + 1
#                 })
        
#         return posts
    
#     def save_generated_posts(self, posts):
#         """Save generated posts to the database.
        
#         Args:
#             posts: List of post dictionaries
            
#         Returns:
#             List of post IDs
#         """
#         post_ids = []
        
#         for post in posts:
#             post_id = save_generated_post(post['content'], post['hashtags'])
#             post_ids.append(post_id)
        
#         return post_ids
    
#     def close(self):
#         """Close analyzer."""
#         if self.analyzer:
#             self.analyzer.close()
import random
import time

class PostGenerator:
    """
    Class responsible for generating LinkedIn posts using predefined templates
    or AI-based generation (expandable to use an actual AI API in the future)
    """
    
    def __init__(self):
        self.templates = [
            "As a professional in the {industry} space, I've been reflecting on {topic}. {key_point}. What are your thoughts on this evolving landscape? {cta}",
            "I recently discovered something interesting about {topic} that changed my perspective. {key_point}. Has anyone else experienced this? {cta}",
            "The future of {topic} is rapidly changing. {key_point}. How is your organization adapting to these shifts? {cta}",
            "{question_hook} When it comes to {topic}, I believe {key_point}. What's your take? {cta}"
        ]
        
        self.key_points = {
            "AI and Machine Learning": [
                "The integration of AI into everyday business processes is no longer optional but essential for staying competitive",
                "Machine learning models are becoming more accessible to non-technical teams, democratizing AI adoption",
                "The ethical implications of AI deployment require thoughtful consideration at every stage of implementation",
                "Real-world AI success depends more on quality data than on algorithm sophistication"
            ],
            "Leadership": [
                "Effective leadership is more about empowering others than showcasing personal success",
                "Transparent communication builds stronger teams than carefully curated messaging",
                "The best leaders maintain a learning mindset regardless of their experience level",
                "Psychological safety is the foundation upon which innovative teams are built"
            ],
            "Career Development": [
                "Skills acquisition has become more important than traditional career ladders",
                "Cross-functional experience often delivers more growth than vertical progression",
                "Continuous learning has transformed from a nice-to-have to a professional necessity",
                "Building a personal brand helps you shape how opportunities find you"
            ]
        }
        
        self.ctas = [
            "I'd love to hear your experiences in the comments below.",
            "Share your insights in the comments!",
            "Let's continue this conversation in the comments section.",
            "If you found this valuable, consider sharing with your network."
        ]
        
        self.question_hooks = [
            "Have you wondered why some {topic} initiatives succeed while others fail?",
            "What if everything we know about {topic} is about to change?",
            "How will {topic} transform your industry in the next five years?",
            "Are you leveraging {topic} to its full potential?"
        ]
        
        self.hashtag_sets = {
            "AI and Machine Learning": ["#ArtificialIntelligence", "#MachineLearning", "#TechTrends", "#FutureOfWork", "#DataScience"],
            "Leadership": ["#Leadership", "#Management", "#BusinessGrowth", "#TeamBuilding", "#ProfessionalDevelopment"],
            "Career Development": ["#CareerAdvice", "#ProfessionalGrowth", "#Networking", "#JobSearch", "#SkillsGap"]
        }
    
    def _get_key_point(self, topic):
        """Get a key point related to the topic or a general one if topic not found"""
        if topic in self.key_points:
            return random.choice(self.key_points[topic])
        
        # Default key points for any topic
        default_points = [
            f"The landscape of {topic} is evolving faster than many realize",
            f"Success in {topic} requires both technical knowledge and soft skills",
            f"The most common misconception about {topic} is that it's too complex for beginners",
            f"Staying current with {topic} trends can give professionals a significant advantage"
        ]
        return random.choice(default_points)
    
    def _get_hashtags(self, topic, count=3):
        """Generate relevant hashtags for the post"""
        if topic in self.hashtag_sets:
            tags = random.sample(self.hashtag_sets[topic], min(count, len(self.hashtag_sets[topic])))
        else:
            # Create generic hashtags based on topic
            topic_words = topic.split()
            topic_hashtags = ["#" + word.capitalize() for word in topic_words]
            generic_tags = ["#Innovation", "#Growth", "#Professional", "#Insights", "#Learning"]
            tags = topic_hashtags + random.sample(generic_tags, min(count, len(generic_tags)))
            tags = tags[:count]
        
        return " ".join(tags)
    
    def _adjust_for_tone(self, content, tone):
        """Adjust content based on the specified tone"""
        # Placeholder for more sophisticated tone adjustment
        # In a real implementation, this could use NLP or more complex rules
        if tone == "Professional":
            return content  # Default templates are professional
        elif tone == "Casual":
            return content.replace("I believe", "I think").replace("reflecting on", "thinking about")
        elif tone == "Inspirational":
            return content + " Together, we can make a difference in this space."
        elif tone == "Educational":
            return "Did you know? " + content
        return content
    
    def generate_posts(self, topic, tone="Professional", target_audience="Professionals", 
                       custom_instructions="", num_variants=1):
        """
        Generate LinkedIn posts based on the given parameters
        
        Args:
            topic (str): The main topic of the post
            tone (str): The desired tone of the post (Professional, Casual, etc.)
            target_audience (str): The target audience for the post
            custom_instructions (str): Any custom instructions for post generation
            num_variants (int): Number of post variants to generate
            
        Returns:
            list: List of dictionaries containing generated posts with content and hashtags
        """
        try:
            # Simulate processing time (remove in production)
            time.sleep(1)
            
            generated_posts = []
            
            for _ in range(num_variants):
                template = random.choice(self.templates)
                
                # Format question hook if present
                question_hook = ""
                if "{question_hook}" in template:
                    raw_hook = random.choice(self.question_hooks)
                    question_hook = raw_hook.format(topic=topic)
                
                # Format the post content
                content = template.format(
                    industry=target_audience.split()[0] if target_audience and " " in target_audience else "professional",
                    topic=topic,
                    key_point=self._get_key_point(topic),
                    cta=random.choice(self.ctas),
                    question_hook=question_hook
                )
                
                # Adjust for tone
                content = self._adjust_for_tone(content, tone)
                
                # Generate hashtags
                hashtags = self._get_hashtags(topic)
                
                generated_posts.append({
                    "content": content,
                    "hashtags": hashtags
                })
            
            return generated_posts
        
        except Exception as e:
            print(f"Error in generate_posts: {str(e)}")
            return []