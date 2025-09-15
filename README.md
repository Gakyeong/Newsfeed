# Newsfeed

### Education News Summarizer & Email Delivery
### Project Overview
This project delivers daily summarized education-focused news articles to users via email. It features two news sources:
    1.RSS Feed — Fetches and summarizes the latest education news headlines and excerpts.
    2.Gmail API — Retrieves full education articles by tags, summarizes them, and sends customized summaries.

Users submit their email address through an interactive Streamlit web interface to receive the summarized news directly in their inbox.

### Why This Project Matters
1. Stay Informed Efficiently: Education professionals, students, and enthusiasts often face information overload. This project condenses relevant news into concise summaries.

2. Personalized Learning: By delivering summarized content on-demand via email, users can access up-to-date educational news without spending time browsing multiple sources.

3. Data Science in Action: This combines real-world data collection (RSS and APIs), natural language processing (NLP) for summarization, and practical application deployment through an easy web interface.

### Approach & Implementation
#### Part 1: RSS Summarizer
1. Data Collection: Use Python's feedparser to read the EdSurge RSS feed, extracting titles, summaries, and links.
2. Summarization: Employ transformer-based NLP models (e.g., facebook/bart-large-cnn via Hugging Face Transformers) to summarize article excerpts.
3. User Input: Build a Streamlit form for users to enter their email.
4. Email Delivery: Use SMTP to send the summarized news as an email to the user.

#### Part 2: Gmail API Summarizer
1. Data Collection: Access the New York Times API to fetch full-text articles from the education section, filtered by relevant tags.
2. Summarization: Apply the same NLP summarization model to condense the article text.
3. Email Delivery: Summaries are emailed similarly as in Part 1.
4. Customization: Potential to filter or personalize based on tags/topics selected.

#### Technologies Used
* Python
* Streamlit — for the web interface
* feedparser — parsing RSS feeds
* Hugging Face Transformers — for summarization
* SMTP (e.g., Gmail SMTP) — for sending emails
* Gmail API — fetching education news articles
* Power Automate