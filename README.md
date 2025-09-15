# Newsfeed

### Education News Summarizer & Email Delivery
### Project Overview
This project delivers daily summarized education-focused news articles to users via email. It features two news sources:
    1.RSS Feed — Fetches and summarizes the latest education news headlines and excerpts.
    2.Gmail API — Retrieves full education articles by tags, summarizes them, and sends customized summaries.

Users receive the summarized news and links directly in their inbox every Monday via GitHub Actions.

### Why This Project Matters
1. Stay Informed Efficiently: Education professionals, students, and enthusiasts often face information overload. This project condenses relevant news into concise summaries.

2. Personalized Learning: By delivering summarized content on-demand via email, users can access up-to-date educational news without spending time browsing multiple sources.

3. Data Science in Action: This combines real-world data collection (RSS and APIs), natural language processing (NLP) for summarization, and practical application deployment through an easy web interface.

### Approach & Implementation
#### Part 1: RSS Aggregation
The pipeline begins by collecting external articles from trusted education sources using Python’s feedparser library. It reads multiple RSS feeds, extracts metadata such as titles, summaries, publication dates, and links, and prepares the content for downstream processing.

#### Part 2: Gmail API Integration
Next, the system connects to the Gmail API to retrieve relevant emails from a personal Gmail account. It filters messages based on sender domains and subject keywords, focusing on education-related content. Extracted data includes subject lines, message bodies, and sender information.

#### Part 3: Tagging & Mapping
Each piece of content—whether from RSS or Gmail—is classified using a source-aware tagging system. This step applies custom logic to assign meaningful tags such as “Policy,” “Research,” or “EdTech,” based on the origin and context of the content. It also maps senders and feed sources to consistent labels for digest clarity.

#### Part 4: NLP Summarization
To make the digest concise and readable, the pipeline uses Hugging Face’s transformers library to summarize long-form content. This step applies either extractive or abstractive summarization models to distill key insights from articles and emails into short, business-friendly blurbs.

#### Part 5: Digest Formatting
Once the content is tagged and summarized, it is formatted into a clean HTML structure suitable for email delivery. This step uses templating and BeautifulSoup to organize summaries, links, and tags into a visually appealing layout that’s easy to scan and share.

#### Part 6: Automated Delivery
Finally, the entire pipeline is scheduled to run automatically every Monday at 8 AM MDT (14:00 UTC) using GitHub Actions. The formatted digest is sent via the Gmail API to a designated recipient, ensuring consistent and timely delivery without manual intervention.

#### Technologies Used
* Python
* feedparser 
* Hugging Face Transformers
* Gmail API 
* GitHub Actions