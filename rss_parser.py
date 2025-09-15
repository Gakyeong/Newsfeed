# %%
import polars as pl
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
#%% check the metadata and entries
# List of RSS feed URLs
rss_urls = [
    "https://www.the74million.org/feed/",
    "https://edsource.org/feed",
    "https://www.k12dive.com/feeds/news/",
    "https://www.edsurge.com/articles_rss",
    # "https://www.forbes.com/education/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Education.xml",
    "https://www.eschoolnews.com/feed/",
    'https://hechingerreport.org/feed/',
    'https://learningpolicyinstitute.org/rss.xml',
    'https://crpe.org/feed/',
    'https://www.ecs.org/newsroom/feed/'
]
#%%
# for rss_url in rss_urls:
#     print(f"\n📡 Fetching feed: {rss_url}")
#     feed = feedparser.parse(rss_url)

#     # Metadata keys
#     print("\n🔎 Feed Metadata Keys:")
#     for key in feed.feed.keys():
#         print("-", key)

#     # Metadata content
#     print("\n📘 Feed Metadata Values:")
#     for key, value in feed.feed.items():
#         print(f"{key}: {value}")

#     print("\n📰 Total Entries:", len(feed.entries))

#     # Shows all available entries 
#     for entry in feed.entries[:1]:
#         print(entry.keys()) 

#     #Loop through top entries
#     for i, entry in enumerate(feed.entries[:5]):
#         print(f"\n📄 Entry {i+1}:")
#         print("Title:", entry.get("title", "N/A"))
#         print("Link:", entry.get("link", "N/A"))
#         print("Published:", entry.get("published", "N/A"))
#         print("Summary:", entry.get("summary", "N/A"))
#         if 'tags' in entry:
#             print("Tags:", [tag.get("term", "N/A") for tag in entry.tags])
#         else:
#             print("Tags: None found")

        
# print("\n✅ All RSS feeds parsed successfully.")
#%%
# The 74
'''dict_keys(['title', 'title_detail', 'links', 'link', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content'])'''

# edsource
'''dict_keys(['title', 'title_detail', 'links', 'link', 'comments', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'wfw_commentrss', 'slash_comments'])'''

# k12dive
'''dict_keys(['title', 'title_detail', 'links', 'link', 'summary', 'summary_detail', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'id', 'guidislink'])'''

# edsurge
'''dict_keys(['title', 'title_detail', 'links', 'link', 'comments', 'authors', 'author', 'author_detail', 'tags', 'published', 'published_parsed', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'media_thumbnail', 'href', 'media_content', 'media_credit', 'credit'])'''

# forbes?
# nytimes 
'''dict_keys(['title', 'title_detail', 'links', 'link', 'id', 'guidislink', 'summary', 'summary_detail', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'media_content', 'media_credit', 'credit'])'''

# eschoolnews
'''dict_keys(['title', 'title_detail', 'links', 'link', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'post-id'])'''
#%%
# Source-based tag mapping
SOURCE_TAGS = {
    'The 74': ['📰News Organizations'],
    'EdSource': ['📰News Organizations'],
    'K-12 Dive': ['📰News Organizations'],
    'EdSurge': ['📰News Organizations'],
    'NYT Education': ['📰News Organizations'],
    'eSchool News': ['📰News Organizations'],
    'The Hechinger Report': ['🏛️ Non-Profits'],
    'Learning Policy Institute': ['🏛️ Non-Profits'],
    'Center on Reinventing Public Education': ['🏛️ Non-Profits'],
    'Education Commission of the States': ['🏛️ State / Legislative Organizations'],
    'NYT > Education' : ['📰News Organizations']
}

#%%

# Define last week's Monday–Sunday range
def get_last_week_range():
    today = datetime.now()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday.date(), last_sunday.date()

def clean_summary(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    # Get visible text, excluding image tags
    return soup.get_text(separator=' ', strip=True)
#%%
# Parse one feed and return structured entries and add tags by source
def parse_feed(feed_url, start_date, end_date):
    feed = feedparser.parse(feed_url)
    rows = []

    source_title = feed.feed.get('title', 'Unknown Source').strip()
    sender_tags = SOURCE_TAGS.get(source_title, [])

    for entry in feed.entries:
        try:
            published_date = datetime(*entry.published_parsed[:6]).date()
        except AttributeError:
            continue

        if not (start_date <= published_date <= end_date):
            continue

        title = entry.title if hasattr(entry, 'title') else 'Untitled'
        link = entry.link if hasattr(entry, 'link') else 'No Link'

        # Clean summary
        raw_summary = getattr(entry, 'summary', '')
        if not raw_summary and hasattr(entry, 'content'):
            raw_summary = entry.content[0].value if entry.content else ''
        cleaned = clean_summary(raw_summary)
        summary = cleaned[:250] if cleaned else 'No Summary'

        # Extract content tags
        content_tags = [tag.term for tag in getattr(entry, 'tags', [])] if hasattr(entry, 'tags') else []
        tags = ', '.join(content_tags) if content_tags else 'Untagged'
        sender_tag_str = ', '.join(sender_tags) if sender_tags else 'Unlabeled'

        rows.append({
            'Source': source_title,
            'Title': title,
            'Date': str(published_date),
            'Link': link,
            'Tags': tags,
            'Sender_Tag': sender_tag_str,
            'Summary': summary
        })

    return rows

#%% check feeds
# Aggregate multiple feeds
def aggregate_feeds(feed_urls):
    start_date, end_date = get_last_week_range()
    all_rows = []
    for url in feed_urls:
        all_rows.extend(parse_feed(url, start_date, end_date))
    return pl.DataFrame(all_rows)


#%%
# Main execution
# if __name__ == "__main__":
#     rss_feeds = [
#         'https://www.the74million.org/feed/',
#         'https://edsource.org/feed',
#         'https://www.k12dive.com/rss/',
#         'https://www.edsurge.com/news/feed',
#         'https://rss.nytimes.com/services/xml/rss/nyt/Education.xml',
#         'https://www.eschoolnews.com/feed/',
#         'https://hechingerreport.org/feed/',
#         'https://learningpolicyinstitute.org/rss.xml',
#         'https://crpe.org/feed/',
#         'https://www.ecs.org/newsroom/feed/'

#     ]

#     df = aggregate_feeds(rss_feeds)
#     print(df)

# %%
