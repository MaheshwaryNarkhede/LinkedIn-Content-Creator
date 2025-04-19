# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# from datetime import datetime, timedelta
# import json
# import os

# # Import project modules
# from src.content_generator import PostGenerator
# from src.feedback_handler import FeedbackHandler
# from src.post_scheduler import PostScheduler
# from src.utils import get_db_connection, save_post_to_db

# # Configure the page
# st.set_page_config(
#     page_title="LinkedIn Content Creator",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # Initialize session state
# if 'current_post_id' not in st.session_state:
#     st.session_state.current_post_id = None
# if 'generated_content' not in st.session_state:
#     st.session_state.generated_content = None
# if 'hashtags' not in st.session_state:
#     st.session_state.hashtags = None
# if 'scheduled_posts' not in st.session_state:
#     st.session_state.scheduled_posts = []

# # Load LinkedIn profiles
# def load_profiles():
#     try:
#         with open("data/profiles.json", "r") as f:
#             profiles_data = json.load(f)
#             # Ensure the profiles data has the expected structure
#             if "profiles" not in profiles_data:
#                 profiles_data = {"profiles": profiles_data if isinstance(profiles_data, list) else []}
#             return profiles_data
#     except FileNotFoundError:
#         return {"profiles": [{"name": "Default Profile", "industry": "Technology", "tone": "Professional"}]}
#     except json.JSONDecodeError:
#         st.error("Error reading profiles.json. Using default profile.")
#         return {"profiles": [{"name": "Default Profile", "industry": "Technology", "tone": "Professional"}]}

# # Save profiles
# def save_profiles(profiles):
#     os.makedirs("data", exist_ok=True)
#     with open("data/profiles.json", "w") as f:
#         json.dump(profiles, f, indent=4)

# # App title and description
# st.title("🚀 LinkedIn Content Creator")
# st.markdown("""
# Generate, analyze, and schedule high-quality LinkedIn posts using AI.
# Monitor performance and improve your content strategy.
# """)

# # Sidebar for navigation
# st.sidebar.title("Navigation")
# page = st.sidebar.radio("Go to", ["Generate Posts", "Scheduled Posts", "Feedback Analysis", "Settings"])

# # Load profiles
# profiles = load_profiles()

# # Initialize handlers
# feedback_handler = FeedbackHandler()
# post_scheduler = PostScheduler()

# # Generate Posts Page
# if page == "Generate Posts":
#     st.header("Generate LinkedIn Posts")
    
#     # Check if profiles["profiles"] exists and is not empty
#     if "profiles" in profiles and profiles["profiles"]:
#         profile_names = [profile["name"] for profile in profiles["profiles"]]
#         selected_profile = st.selectbox("Select LinkedIn Profile", profile_names)
#         profile_data = next((p for p in profiles["profiles"] if p["name"] == selected_profile), None)
        
#         if profile_data:
#             st.subheader("Post Configuration")
#             col1, col2 = st.columns(2)
#             with col1:
#                 topic = st.text_input("Topic", "AI and Machine Learning")
#                 tone_options = ["Professional", "Casual", "Inspirational", "Educational"]
#                 default_tone = profile_data.get("tone", "Professional")
#                 # Make sure default_tone is in tone_options
#                 if default_tone not in tone_options:
#                     default_tone = "Professional"
#                 tone = st.selectbox("Tone", tone_options, 
#                                     index=tone_options.index(default_tone))
#             with col2:
#                 include_hashtags = st.checkbox("Include Hashtags", value=True)
#                 post_length = st.select_slider("Post Length", 
#                                                options=["Short (100-200 chars)", "Medium (200-400 chars)", "Long (400-700 chars)"],
#                                                value="Medium (200-400 chars)")

#             if st.button("Generate Post"):
#                 with st.spinner("Generating LinkedIn post..."):
#                     try:
#                         generator = PostGenerator()
#                         length_range = {"Short": (100, 200), "Medium": (200, 400), "Long": (400, 700)}[post_length.split()[0]]
                        
#                         # Check if generate_post method exists in PostGenerator
#                         if hasattr(generator, 'generate_post'):
#                             content, hashtags = generator.generate_post(topic, profile_data["industry"], tone, include_hashtags, length_range)
#                         else:
#                             # Use generate_posts method instead (from your provided code)
#                             posts = generator.generate_posts(topic=topic, 
#                                                            tone=tone, 
#                                                            target_audience=profile_data.get("industry", "professionals"), 
#                                                            num_variants=1)
#                             if posts and len(posts) > 0:
#                                 content = posts[0].get('content', '')
#                                 hashtags = posts[0].get('hashtags', '') if include_hashtags else ""
#                             else:
#                                 content = "Failed to generate post content."
#                                 hashtags = ""
                                
#                         post_id = save_post_to_db(content, hashtags if include_hashtags else "", selected_profile, topic, tone)
#                         st.session_state.current_post_id = post_id
#                         st.session_state.generated_content = content
#                         st.session_state.hashtags = hashtags if include_hashtags else ""
#                     except Exception as e:
#                         st.error(f"Error generating post: {str(e)}")
#                         st.session_state.generated_content = f"Error generating post: {str(e)}"
#                         st.session_state.hashtags = ""
#         else:
#             st.error("Selected profile not found. Please check profiles configuration.")
#     else:
#         st.error("No profiles available. Please add a profile in the Settings page.")

#     if st.session_state.generated_content:
#         st.subheader("Generated Post")
#         with st.container(border=True):
#             st.markdown(st.session_state.generated_content)
#             if st.session_state.hashtags:
#                 st.markdown("---")
#                 st.markdown(st.session_state.hashtags)

#         col1, col2 = st.columns(2)
#         with col1:
#             st.subheader("Schedule Post")
#             schedule_date = st.date_input("Date", datetime.now() + timedelta(days=1))
#             schedule_time = st.time_input("Time", datetime.now().time())
#             scheduled_datetime = datetime.combine(schedule_date, schedule_time)
#             if st.button("Schedule Post"):
#                 post_scheduler.schedule_post(st.session_state.current_post_id, scheduled_datetime)
#                 st.success(f"Post scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
#                 st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
#         with col2:
#             st.subheader("Provide Feedback")
#             feedback_score = st.slider("Quality Score", 1, 5, 3)
#             feedback_text = st.text_area("Feedback Comments", "")
#             if st.button("Submit Feedback"):
#                 if feedback_handler.record_feedback(st.session_state.current_post_id, feedback_score, feedback_text):
#                     st.success("Feedback recorded. Thank you!")
#                 else:
#                     st.error("Failed to record feedback.")

# # Scheduled Posts Page
# elif page == "Scheduled Posts":
#     st.header("Scheduled Posts")
#     scheduled_posts = post_scheduler.get_scheduled_posts()
#     st.session_state.scheduled_posts = scheduled_posts
#     if not scheduled_posts:
#         st.info("No posts scheduled.")
#     else:
#         posts_df = pd.DataFrame(scheduled_posts)
#         posts_df = posts_df.rename(columns={
#             "id": "Post ID", "content": "Content", "scheduled_time": "Scheduled Time",
#             "profile": "Profile", "status": "Status"
#         })
#         posts_df["Content"] = posts_df["Content"].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)
#         st.dataframe(posts_df, use_container_width=True, hide_index=True)

#         selected_post_id = st.selectbox("Select post to view details or reschedule", 
#                                         options=[post["id"] for post in scheduled_posts],
#                                         format_func=lambda x: f"Post {x}")
#         selected_post = next((post for post in scheduled_posts if post["id"] == selected_post_id), None)
#         if selected_post:
#             st.subheader("Post Details")
#             with st.container(border=True):
#                 st.markdown(selected_post["content"])
#                 if selected_post.get("hashtags"):
#                     st.markdown("---")
#                     st.markdown(selected_post["hashtags"])
#             st.text(f"Scheduled for: {selected_post['scheduled_time']}")
#             st.text(f"Status: {selected_post['status']}")

#             if selected_post["status"] == "Scheduled":
#                 st.subheader("Reschedule Post")
#                 new_date = st.date_input("New Date", datetime.strptime(selected_post["scheduled_time"], "%Y-%m-%d %H:%M:%S"))
#                 new_time = st.time_input("New Time")
#                 new_datetime = datetime.combine(new_date, new_time)
#                 if st.button("Reschedule"):
#                     if post_scheduler.reschedule_post(selected_post_id, new_datetime):
#                         st.success(f"Post rescheduled for {new_datetime.strftime('%Y-%m-%d %H:%M')}")
#                         st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
#                         st.experimental_rerun()
#                     else:
#                         st.error("Failed to reschedule post.")

#                 if st.button("Cancel Post"):
#                     if post_scheduler.cancel_post(selected_post_id):
#                         st.success("Post cancelled successfully.")
#                         st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
#                         st.experimental_rerun()
#                     else:
#                         st.error("Failed to cancel post.")

# # Feedback Analysis Page
# elif page == "Feedback Analysis":
#     st.header("Feedback Analysis")
#     feedback_summary = feedback_handler.get_feedback_summary()
#     if feedback_summary["total_feedback"] == 0:
#         st.info("No feedback data available.")
#     else:
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("Total Posts with Feedback", feedback_summary["total_feedback"])
#         with col2:
#             avg_score = feedback_summary["average_score"]
#             if avg_score:
#                 st.metric("Average Feedback Score", f"{avg_score:.2f}/5.00")

#         st.subheader("Feedback Score Distribution")
#         scores = list(feedback_summary["score_distribution"].keys())
#         counts = list(feedback_summary["score_distribution"].values())
#         fig, ax = plt.subplots()
#         ax.bar(scores, counts, color='skyblue')
#         ax.set_xlabel('Feedback Score')
#         ax.set_ylabel('Count')
#         ax.set_xticks(scores)
#         st.pyplot(fig)

#         st.subheader("Recent Feedback History")
#         feedback_history = feedback_handler.get_feedback_history(limit=10)
#         for feedback in feedback_history:
#             with st.expander(f"Post from {feedback['generated_at']} - Score: {feedback['feedback_score']}/5"):
#                 st.markdown(feedback["content"])
#                 if feedback["hashtags"]:
#                     st.markdown("---")
#                     st.markdown(feedback["hashtags"])
#                 if feedback["feedback_text"]:
#                     st.markdown("### Feedback Comments")
#                     st.info(feedback["feedback_text"])

# # Settings Page
# elif page == "Settings":
#     st.header("Settings")
#     st.subheader("LinkedIn Profile Management")

#     if "profiles" in profiles and profiles["profiles"]:
#         for i, profile in enumerate(profiles["profiles"]):
#             with st.expander(f"{profile['name']}"):
#                 st.write(f"Industry: {profile.get('industry', 'Not specified')}")
#                 st.write(f"Default Tone: {profile.get('tone', 'Professional')}")
#                 if st.button(f"Delete Profile", key=f"delete_{i}"):
#                     profiles["profiles"].pop(i)
#                     save_profiles(profiles)
#                     st.success("Profile deleted.")
#                     st.experimental_rerun()

#     st.subheader("Add New Profile")
#     with st.form("add_profile_form"):
#         name = st.text_input("Profile Name")
#         industry = st.text_input("Industry")
#         tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Educational"])
#         submitted = st.form_submit_button("Add Profile")
#         if submitted:
#             if "profiles" not in profiles:
#                 profiles["profiles"] = []
#             profiles["profiles"].append({"name": name, "industry": industry, "tone": tone})
#             save_profiles(profiles)
#             st.success(f"Profile '{name}' added.")
#             st.experimental_rerun()
# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# from datetime import datetime, timedelta
# import json
# import os

# # Import project modules
# from src.content_generator import PostGenerator
# from src.feedback_handler import FeedbackHandler
# from src.post_scheduler import PostScheduler
# from src.utils import get_db_connection, save_generated_post

# # Configure the page
# st.set_page_config(
#     page_title="LinkedIn Content Creator",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # Initialize session state
# if 'current_post_id' not in st.session_state:
#     st.session_state.current_post_id = None
# if 'generated_content' not in st.session_state:
#     st.session_state.generated_content = None
# if 'hashtags' not in st.session_state:
#     st.session_state.hashtags = None
# if 'scheduled_posts' not in st.session_state:
#     st.session_state.scheduled_posts = []

# # Load LinkedIn profiles
# def load_profiles():
#     try:
#         with open("data/profiles.json", "r") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {"profiles": [{"name": "Default Profile", "industry": "Technology", "tone": "Professional"}]}

# # Save profiles
# def save_profiles(profiles):
#     os.makedirs("data", exist_ok=True)
#     with open("data/profiles.json", "w") as f:
#         json.dump(profiles, f, indent=4)

# # App title and description
# st.title("🚀 LinkedIn Content Creator")
# st.markdown("""
# Generate, analyze, and schedule high-quality LinkedIn posts using AI.
# Monitor performance and improve your content strategy.
# """)

# # Sidebar for navigation
# st.sidebar.title("Navigation")
# page = st.sidebar.radio("Go to", ["Generate Posts", "Scheduled Posts", "Feedback Analysis", "Settings"])

# # Load profiles
# profiles = load_profiles()

# # Initialize handlers
# feedback_handler = FeedbackHandler()
# post_scheduler = PostScheduler()

# # Generate Posts Page
# if page == "Generate Posts":
#     st.header("Generate LinkedIn Posts")
#     profile_names = [profile["name"] for profile in profiles["profiles"]]
#     selected_profile = st.selectbox("Select LinkedIn Profile", profile_names)
#     profile_data = next((p for p in profiles["profiles"] if p["name"] == selected_profile), None)

#     st.subheader("Post Configuration")
#     col1, col2 = st.columns(2)
#     with col1:
#         topic = st.text_input("Topic", "AI and Machine Learning")
#         tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Educational"], 
#                             index=["Professional", "Casual", "Inspirational", "Educational"].index(profile_data["tone"]))
#     with col2:
#         include_hashtags = st.checkbox("Include Hashtags", value=True)
#         post_length = st.select_slider("Post Length", 
#                                        options=["Short (100-200 chars)", "Medium (200-400 chars)", "Long (400-700 chars)"],
#                                        value="Medium (200-400 chars)")

#     if st.button("Generate Post"):
#         try:
#             with st.spinner("Generating LinkedIn post..."):
#                 generator = PostGenerator()
#                 length_range = {"Short": (100, 200), "Medium": (200, 400), "Long": (400, 700)}[post_length.split()[0]]
                
#                 # Adapt to use generate_posts method from PostGenerator
#                 post_variants = generator.generate_posts(
#                     topic=topic, 
#                     tone=tone,
#                     target_audience=profile_data["industry"],
#                     custom_instructions=f"Length should be between {length_range[0]} and {length_range[1]} characters"
#                 )
                
#                 if post_variants and len(post_variants) > 0:
#                     content = post_variants[0]['content']
#                     hashtags = post_variants[0]['hashtags'] if include_hashtags else ""
#                     post_id = save_generated_post(content, hashtags)
                    
#                     st.session_state.current_post_id = post_id
#                     st.session_state.generated_content = content
#                     st.session_state.hashtags = hashtags
#                 else:
#                     st.error("Failed to generate post content.")
#         except Exception as e:
#             st.error(f"Error generating post: {str(e)}")

#     if st.session_state.generated_content:
#         st.subheader("Generated Post")
#         with st.container(border=True):
#             st.markdown(st.session_state.generated_content)
#             if st.session_state.hashtags:
#                 st.markdown("---")
#                 st.markdown(st.session_state.hashtags)

#         col1, col2 = st.columns(2)
#         with col1:
#             st.subheader("Schedule Post")
#             schedule_date = st.date_input("Date", datetime.now() + timedelta(days=1))
#             schedule_time = st.time_input("Time", datetime.now().time())
#             scheduled_datetime = datetime.combine(schedule_date, schedule_time)
#             if st.button("Schedule Post"):
#                 post_scheduler.schedule_post(st.session_state.current_post_id, scheduled_datetime)
#                 st.success(f"Post scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
#                 st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
#         with col2:
#             st.subheader("Provide Feedback")
#             feedback_score = st.slider("Quality Score", 1, 5, 3)
#             feedback_text = st.text_area("Feedback Comments", "")
#             if st.button("Submit Feedback"):
#                 if feedback_handler.record_feedback(st.session_state.current_post_id, feedback_score, feedback_text):
#                     st.success("Feedback recorded. Thank you!")
#                 else:
#                     st.error("Failed to record feedback.")

# # Scheduled Posts Page
# elif page == "Scheduled Posts":
#     st.header("Scheduled Posts")
#     scheduled_posts = post_scheduler.get_scheduled_posts()
#     st.session_state.scheduled_posts = scheduled_posts
#     if not scheduled_posts:
#         st.info("No posts scheduled.")
#     else:
#         posts_df = pd.DataFrame(scheduled_posts)
#         posts_df = posts_df.rename(columns={
#             "id": "Post ID", "content": "Content", "scheduled_time": "Scheduled Time",
#             "profile": "Profile", "status": "Status"
#         })
#         posts_df["Content"] = posts_df["Content"].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)
#         st.dataframe(posts_df, use_container_width=True, hide_index=True)

#         selected_post_id = st.selectbox("Select post to view details or reschedule", 
#                                         options=[post["id"] for post in scheduled_posts],
#                                         format_func=lambda x: f"Post {x}")
#         selected_post = next((post for post in scheduled_posts if post["id"] == selected_post_id), None)
#         if selected_post:
#             st.subheader("Post Details")
#             with st.container(border=True):
#                 st.markdown(selected_post["content"])
#                 if selected_post.get("hashtags"):
#                     st.markdown("---")
#                     st.markdown(selected_post["hashtags"])
#             st.text(f"Scheduled for: {selected_post['scheduled_time']}")
#             st.text(f"Status: {selected_post['status']}")

#             if selected_post["status"] == "Scheduled":
#                 st.subheader("Reschedule Post")
#                 new_date = st.date_input("New Date", datetime.strptime(selected_post["scheduled_time"], "%Y-%m-%d %H:%M:%S"))
#                 new_time = st.time_input("New Time")
#                 new_datetime = datetime.combine(new_date, new_time)
#                 if st.button("Reschedule"):
#                     if post_scheduler.reschedule_post(selected_post_id, new_datetime):
#                         st.success(f"Post rescheduled for {new_datetime.strftime('%Y-%m-%d %H:%M')}")
#                         st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
#                         st.experimental_rerun()
#                     else:
#                         st.error("Failed to reschedule post.")

#                 if st.button("Cancel Post"):
#                     if post_scheduler.cancel_post(selected_post_id):
#                         st.success("Post cancelled successfully.")
#                         st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
#                         st.experimental_rerun()
#                     else:
#                         st.error("Failed to cancel post.")

# # Feedback Analysis Page
# elif page == "Feedback Analysis":
#     st.header("Feedback Analysis")
#     feedback_summary = feedback_handler.get_feedback_summary()
#     if feedback_summary["total_feedback"] == 0:
#         st.info("No feedback data available.")
#     else:
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("Total Posts with Feedback", feedback_summary["total_feedback"])
#         with col2:
#             avg_score = feedback_summary["average_score"]
#             if avg_score:
#                 st.metric("Average Feedback Score", f"{avg_score:.2f}/5.00")

#         st.subheader("Feedback Score Distribution")
#         scores = list(feedback_summary["score_distribution"].keys())
#         counts = list(feedback_summary["score_distribution"].values())
#         fig, ax = plt.subplots()
#         ax.bar(scores, counts, color='skyblue')
#         ax.set_xlabel('Feedback Score')
#         ax.set_ylabel('Count')
#         ax.set_xticks(scores)
#         st.pyplot(fig)

#         st.subheader("Recent Feedback History")
#         feedback_history = feedback_handler.get_feedback_history(limit=10)
#         for feedback in feedback_history:
#             with st.expander(f"Post from {feedback['generated_at']} - Score: {feedback['feedback_score']}/5"):
#                 st.markdown(feedback["content"])
#                 if feedback["hashtags"]:
#                     st.markdown("---")
#                     st.markdown(feedback["hashtags"])
#                 if feedback["feedback_text"]:
#                     st.markdown("### Feedback Comments")
#                     st.info(feedback["feedback_text"])

# # Settings Page
# elif page == "Settings":
#     st.header("Settings")
#     st.subheader("LinkedIn Profile Management")

#     if profiles["profiles"]:
#         for i, profile in enumerate(profiles["profiles"]):
#             with st.expander(f"{profile['name']}"):
#                 st.write(f"Industry: {profile['industry']}")
#                 st.write(f"Default Tone: {profile['tone']}")
#                 if st.button(f"Delete Profile", key=f"delete_{i}"):
#                     profiles["profiles"].pop(i)
#                     save_profiles(profiles)
#                     st.success("Profile deleted.")
#                     st.experimental_rerun()

#     st.subheader("Add New Profile")
#     with st.form("add_profile_form"):
#         name = st.text_input("Profile Name")
#         industry = st.text_input("Industry")
#         tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Educational"])
#         submitted = st.form_submit_button("Add Profile")
#         if submitted:
#             profiles["profiles"].append({"name": name, "industry": industry, "tone": tone})
#             save_profiles(profiles)
#             st.success(f"Profile '{name}' added.")
#             st.experimental_rerun()
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import os

# Import project modules
from src.content_generator import PostGenerator
from src.feedback_handler import FeedbackHandler
from src.post_scheduler import PostScheduler
from src.utils import get_db_connection, save_post_to_db

# Configure the page
st.set_page_config(
    page_title="LinkedIn Content Creator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if 'current_post_id' not in st.session_state:
    st.session_state.current_post_id = None
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'hashtags' not in st.session_state:
    st.session_state.hashtags = None
if 'scheduled_posts' not in st.session_state:
    st.session_state.scheduled_posts = []

# Load LinkedIn profiles
def load_profiles():
    try:
        with open("data/profiles.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"profiles": [{"name": "Default Profile", "industry": "Technology", "tone": "Professional"}]}

# Save profiles
def save_profiles(profiles):
    os.makedirs("data", exist_ok=True)
    with open("data/profiles.json", "w") as f:
        json.dump(profiles, f, indent=4)

# App title and description
st.title("🚀 LinkedIn Content Creator")
st.markdown("""
Generate, analyze, and schedule high-quality LinkedIn posts using AI.
Monitor performance and improve your content strategy.
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Generate Posts", "Scheduled Posts", "Feedback Analysis", "Settings"])

# Load profiles
profiles = load_profiles()

# Initialize handlers
feedback_handler = FeedbackHandler()
post_scheduler = PostScheduler()

# Generate Posts Page
if page == "Generate Posts":
    st.header("Generate LinkedIn Posts")
    profile_names = [profile["name"] for profile in profiles["profiles"]]
    selected_profile = st.selectbox("Select LinkedIn Profile", profile_names)
    profile_data = next((p for p in profiles["profiles"] if p["name"] == selected_profile), None)

    st.subheader("Post Configuration")
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Topic", "AI and Machine Learning")
        tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Educational"], 
                            index=["Professional", "Casual", "Inspirational", "Educational"].index(profile_data["tone"]))
    with col2:
        target_audience = st.text_input("Target Audience", f"Professionals in the {profile_data['industry']} industry")
        custom_instructions = st.text_area("Custom Instructions", f"Post length should be medium (200-400 characters).")

    if st.button("Generate Post"):
        with st.spinner("Generating LinkedIn post..."):
            try:
                # Use the correct method from PostGenerator
                generator = PostGenerator()
                
                # Use generate_posts method with the appropriate parameters
                generated_posts = generator.generate_posts(
                    topic=topic,
                    tone=tone,
                    target_audience=target_audience,
                    custom_instructions=custom_instructions,
                    num_variants=1  # Just generate one post for now
                )
                
                if generated_posts and len(generated_posts) > 0:
                    # Get the first post from the generated list
                    post = generated_posts[0]
                    content = post['content']
                    hashtags = post['hashtags']
                    
                    # Save the post to the database
                    post_id = save_post_to_db(content, hashtags)
                    
                    # Update session state
                    st.session_state.current_post_id = post_id
                    st.session_state.generated_content = content
                    st.session_state.hashtags = hashtags
                else:
                    st.error("Failed to generate post content.")
            except Exception as e:
                st.error(f"Error generating post: {str(e)}")

    if st.session_state.generated_content:
        st.subheader("Generated Post")
        with st.container(border=True):
            st.markdown(st.session_state.generated_content)
            if st.session_state.hashtags:
                st.markdown("---")
                st.markdown(st.session_state.hashtags)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Schedule Post")
            schedule_date = st.date_input("Date", datetime.now() + timedelta(days=1))
            schedule_time = st.time_input("Time", datetime.now().time())
            scheduled_datetime = datetime.combine(schedule_date, schedule_time)
            if st.button("Schedule Post"):
                post_scheduler.schedule_post(st.session_state.current_post_id, scheduled_datetime)
                st.success(f"Post scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
                st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
        with col2:
            st.subheader("Provide Feedback")
            feedback_score = st.slider("Quality Score", 1, 5, 3)
            feedback_text = st.text_area("Feedback Comments", "")
            if st.button("Submit Feedback"):
                if feedback_handler.record_feedback(st.session_state.current_post_id, feedback_score, feedback_text):
                    st.success("Feedback recorded. Thank you!")
                else:
                    st.error("Failed to record feedback.")

# Scheduled Posts Page
elif page == "Scheduled Posts":
    st.header("Scheduled Posts")
    scheduled_posts = post_scheduler.get_scheduled_posts()
    st.session_state.scheduled_posts = scheduled_posts
    if not scheduled_posts:
        st.info("No posts scheduled.")
    else:
        posts_df = pd.DataFrame(scheduled_posts)
        posts_df = posts_df.rename(columns={
            "id": "Post ID", "content": "Content", "scheduled_time": "Scheduled Time",
            "profile": "Profile", "status": "Status"
        })
        posts_df["Content"] = posts_df["Content"].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)
        st.dataframe(posts_df, use_container_width=True, hide_index=True)

        selected_post_id = st.selectbox("Select post to view details or reschedule", 
                                        options=[post["id"] for post in scheduled_posts],
                                        format_func=lambda x: f"Post {x}")
        selected_post = next((post for post in scheduled_posts if post["id"] == selected_post_id), None)
        if selected_post:
            st.subheader("Post Details")
            with st.container(border=True):
                st.markdown(selected_post["content"])
                if selected_post.get("hashtags"):
                    st.markdown("---")
                    st.markdown(selected_post["hashtags"])
            st.text(f"Scheduled for: {selected_post['scheduled_time']}")
            st.text(f"Status: {selected_post['status']}")

            if selected_post["status"] == "Scheduled":
                st.subheader("Reschedule Post")
                new_date = st.date_input("New Date", datetime.strptime(selected_post["scheduled_time"], "%Y-%m-%d %H:%M:%S"))
                new_time = st.time_input("New Time")
                new_datetime = datetime.combine(new_date, new_time)
                if st.button("Reschedule"):
                    if post_scheduler.reschedule_post(selected_post_id, new_datetime):
                        st.success(f"Post rescheduled for {new_datetime.strftime('%Y-%m-%d %H:%M')}")
                        st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
                        st.experimental_rerun()
                    else:
                        st.error("Failed to reschedule post.")

                if st.button("Cancel Post"):
                    if post_scheduler.cancel_post(selected_post_id):
                        st.success("Post cancelled successfully.")
                        st.session_state.scheduled_posts = post_scheduler.get_scheduled_posts()
                        st.experimental_rerun()
                    else:
                        st.error("Failed to cancel post.")

# Feedback Analysis Page
elif page == "Feedback Analysis":
    st.header("Feedback Analysis")
    feedback_summary = feedback_handler.get_feedback_summary()
    if feedback_summary["total_feedback"] == 0:
        st.info("No feedback data available.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Posts with Feedback", feedback_summary["total_feedback"])
        with col2:
            avg_score = feedback_summary["average_score"]
            if avg_score:
                st.metric("Average Feedback Score", f"{avg_score:.2f}/5.00")

        st.subheader("Feedback Score Distribution")
        scores = list(feedback_summary["score_distribution"].keys())
        counts = list(feedback_summary["score_distribution"].values())
        fig, ax = plt.subplots()
        ax.bar(scores, counts, color='skyblue')
        ax.set_xlabel('Feedback Score')
        ax.set_ylabel('Count')
        ax.set_xticks(scores)
        st.pyplot(fig)

        st.subheader("Recent Feedback History")
        feedback_history = feedback_handler.get_feedback_history(limit=10)
        for feedback in feedback_history:
            with st.expander(f"Post from {feedback['generated_at']} - Score: {feedback['feedback_score']}/5"):
                st.markdown(feedback["content"])
                if feedback["hashtags"]:
                    st.markdown("---")
                    st.markdown(feedback["hashtags"])
                if feedback["feedback_text"]:
                    st.markdown("### Feedback Comments")
                    st.info(feedback["feedback_text"])

# Settings Page
elif page == "Settings":
    st.header("Settings")
    st.subheader("LinkedIn Profile Management")

    if profiles["profiles"]:
        for i, profile in enumerate(profiles["profiles"]):
            with st.expander(f"{profile['name']}"):
                st.write(f"Industry: {profile['industry']}")
                st.write(f"Default Tone: {profile['tone']}")
                if st.button(f"Delete Profile", key=f"delete_{i}"):
                    profiles["profiles"].pop(i)
                    save_profiles(profiles)
                    st.success("Profile deleted.")
                    st.experimental_rerun()

    st.subheader("Add New Profile")
    with st.form("add_profile_form"):
        name = st.text_input("Profile Name")
        industry = st.text_input("Industry")
        tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Educational"])
        submitted = st.form_submit_button("Add Profile")
        if submitted:
            profiles["profiles"].append({"name": name, "industry": industry, "tone": tone})
            save_profiles(profiles)
            st.success(f"Profile '{name}' added.")
            st.experimental_rerun()