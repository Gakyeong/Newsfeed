#%%
# pip install torch
#%%
from rss_parser import aggregate_feeds
from gmail_parser import fetch_gmail_entries
from transformers import pipeline
import re
from collections import defaultdict
from email_sender import format_digest_as_html, send_digest_email
#%%
RSS_FEEDS = [
    'https://www.the74million.org/feed/',
    'https://edsource.org/feed',
    'https://www.k12dive.com/rss/',
    'https://www.edsurge.com/news/feed',
    'https://rss.nytimes.com/services/xml/rss/nyt/Education.xml',
    'https://www.eschoolnews.com/feed/',
    'https://hechingerreport.org/feed/',
    'https://learningpolicyinstitute.org/rss.xml',
    'https://crpe.org/feed/',
    'https://www.ecs.org/newsroom/feed/'
]

#%%
def get_all_entries():
    rss_entries = aggregate_feeds(RSS_FEEDS).to_dicts()
    gmail_entries = fetch_gmail_entries()

    def format_entry(entry, is_rss=True):
        return {
            'Source': entry['Source'],
            'Title': entry['Title'],
            'Date': entry['Date'],
            'Link': entry['Link'],
            'Sender Tags': entry['Sender_Tag'] if is_rss else entry['Sender Tags'],
            'Content': entry['Summary'] if is_rss else entry['Full_content']
        }

    return [format_entry(e, True) for e in rss_entries] + [format_entry(e, False) for e in gmail_entries]

#%%
def group_entries_by_tag(entries):
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry['Sender Tags']].append(entry)
    return grouped

#%%
def clean_text(text):
    if not text:
        return ""

    patterns = [
        r'https?://\S+',  # URLs
        r'<[^>]+>',       # HTML tags
        r'[^\x00-\x7F]+', # non-ASCII
        r'[\*\|]',        # stray symbols
        r'\(\s*\)',       # empty parentheses
        r'-{3,}', r'•', r'‌+',
        r'View in browser.*?\n', r'Unsubscribe.*?\n',
        r'\b(Subscribe|Donate|Register|Buy now|Shop|Click|Tap|Visit|Explore)\b.*?\n',
        r'\b(Email not displaying correctly|Trouble viewing this email)\b.*?\n',
        r'\b(Manage your preferences|Update your profile)\b.*?\n',
        r'\b(STORIES EVERYONE\'S READING THIS WEEK.*?)\n',
        r'\b(Funding Available for PTA Programs.*?)\n',
        r'\b(New Special Report.*?)\n',
        r'\b(Postsecondary and workforce category icon.*?)\n',
        r'\b(Sponsored|ADVERTISEMENT|Forward to a friend|To ensure delivery|You received this email|Preferences|Privacy policy|©.*?)\n'
    ]

    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    return re.sub(r'\s+', ' ', text).strip()

#%%
summarizer = pipeline("summarization", model="google/long-t5-tglobal-base")

def summarize_text(text, min_ratio=0.1, max_ratio=0.25, hard_max=250):
    text = clean_text(text)
    if not text:
        return "No content to summarize"

    try:
        input_length = len(text.split())
        if input_length > 900:
            text = " ".join(text.split()[:900])
            input_length = 900

        max_length = min(int(input_length * max_ratio), hard_max)
        min_length = max(int(input_length * min_ratio), 30)
        if min_length >= max_length:
            min_length = max_length - 10 if max_length > 40 else max_length - 1

        max_length = min(max_length, 512)

        result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return result[0]['summary_text']
    except Exception as e:
        print(f"Summarization failed: {e}")
        return "Summary unavailable"

#%%
rewriter = pipeline("text2text-generation", model="google/flan-t5-base")

def refine_summary_with_model(text, group_name=None):
    if not text or text == "Summary unavailable":
        return text

    prompt = f"Rewrite the following summary to improve grammar and clarity:\n\n{text}"
    try:
        result = rewriter(prompt, max_new_tokens=150, do_sample=False)
        refined = result[0]['generated_text']
        if refined.strip().lower().startswith("rewrite") or len(refined.split()) < 10:
            return text
        return refined
    except Exception as e:
        return text

#%%
def summarize_grouped_entries(grouped_entries, preview=False):
    digest = []

    for group, items in grouped_entries.items():
        unique_texts = list(set(clean_text(item.get('Content', '')) for item in items if item.get('Content')))
        combined_text = "\n\n".join(unique_texts)

        # if preview:
        #     print(f"\n--- Preview for Group: {group} ---\n{combined_text[:1000]}\n")

        summary = summarize_text(combined_text) if combined_text else "No content to summarize"
        refined_summary = refine_summary_with_model(summary, group)

        digest.append({
            'Group': group,
            'Summary': refined_summary,
            'Items': items,
            'Count': len(items)
        })

    return digest

#%%
def print_digest(digest):
    for section in digest:
        print(f"\n🗂️ Group: {section['Group']}")
        summary = section['Summary']
        if summary == "Summary unavailable":
            print("🧠 Summary unavailable. Showing combined text preview instead:\n")
            combined_text = "\n\n".join(clean_text(item.get('Content', '')) for item in section['Items'] if item.get('Content'))
            print(combined_text[:500] + "...")
        else:
            print(f"🧠 Summary: {summary}\n")

        for item in section['Items']:
            print(f"- {item['Title']}")
            print(f"  Date: {item['Date']}")
            print(f"  Source: {item['Source']}")
            link = item.get('Link')
            if isinstance(link, list) and link:
                print("  Links:")
                for l in link:
                    print(f"    • {l}")
            elif isinstance(link, str) and link != 'N/A':
                print(f"  Link: {link}")
            else:
                print("  Link: N/A")
        print('-' * 80)

#%%
if __name__ == '__main__':
    entries = get_all_entries()
    grouped = group_entries_by_tag(entries)
    digest = summarize_grouped_entries(grouped, preview=True)
    # print_digest(digest)

    html_content = format_digest_as_html(digest)
    send_digest_email(html_content)

# %%
