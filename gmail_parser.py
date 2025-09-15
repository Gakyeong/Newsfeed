#%%
# pip install torch
# %%
import os.path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from bs4 import BeautifulSoup
from rss_parser import get_last_week_range
from email.utils import parseaddr,parsedate_to_datetime
from urllib.parse import unquote
import json

#%% Authorization in local  : Handles authentication and token setup
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
#           'https://www.googleapis.com/auth/gmail.send']

# def get_credentials():
#     creds = None
#     token_path = 'token.pickle'

#     if os.path.exists(token_path):
#         try:
#             with open(token_path, 'rb') as token:
#                 creds = pickle.load(token)
#         except Exception:
#             os.remove(token_path)  # Remove corrupted token

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             try:
#                 creds.refresh(Request())
#             except Exception:
#                 os.remove(token_path)
#                 return get_credentials()
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#             creds = flow.run_local_server(port=8080)

#         with open(token_path, 'wb') as token:
#             pickle.dump(creds, token)

#     return creds
#%%
# with open('token.pickle', 'rb') as f:
#     encoded = base64.b64encode(f.read()).decode('utf-8')
#     print(encoded)

#%% Authorization - service account 
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
#%%
def get_credentials():
    creds = None
    if 'GMAIL_TOKEN_PICKLE' in os.environ:
        print("🔐 Loading token from GitHub Secrets")
        token_bytes = base64.b64decode(os.environ['GMAIL_TOKEN_PICKLE'])
        creds = pickle.loads(token_bytes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("❌ Token is missing or invalid. Run locally to regenerate.")

    return creds

# %% service : Builds Gmail API service object
def get_gmail_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)
#%%
# Your explicit mapping table
DOMAIN_TO_COMPANY = {
    "ben@whiteboardadvisors.com": "WhiteBoard Advisors",
    "community@chalkbeat.org": "Chalkbeat",
    "ecs@ecs.org": "Education Commission of the States",
    "ed.gov@info.ed.gov": "U.S. Department of Education",
    "edweekevents@mail.edweek.org": "Education Week", 
    "hello@mail.edweek.org":"Education Week", 
    "hmheducation@hmhco.com":"HMH",
    "info@brookings.edu": "Brookings Institution",
    "learn@mail.edweek.org": "Education Week",
    "mail@amplify.com": "Amplify",
    "matt.tower@whiteboardadvisors.com": "WhiteBoard Advisors",
    "national@chalkbeat.org": "Chalkbeat",
    "newsletters@mail.edweek.org":"Education Week", 
    "newsletters@mail.marketbrief.edweek.org": "Education Week",
    "no-reply@info.ed.gov":"U.S. Department of Education",
    "sponsors@chalkbeat.org": "Chalkbeat", 
    "thegadfly@fordhaminstitute.org": "Thomas B. Fordham Institute", 
    "txtea@public.govdelivery.com": "Texas Education Agency"
}

SOURCE_TAGS = {
    "WhiteBoard Advisors":"🏛️ Non-Profits" ,
    "Chalkbeat": "📰 News Organizations",
    "Education Commission of the States": "🏛️ State / Legislative Organizations",
    "U.S. Department of Education": "🏢 Government",
    "Education Week": "📰 News Organizations",
    "HMH": "📘 Competitor Newsletters",
    "Brookings Institution": "🏛️ Non-Profits",
    "Amplify": "📘 Competitor Newsletters",
    "Thomas B. Fordham Institute": "🏛️ Non-Profits", 
    "Texas Education Agency": "🏢 Government" 
}


#%% parse: Extracts structured email data
def get_header(headers, name):
    return next((h['value'] for h in headers if h['name'] == name), f'No {name}')
#%%
def get_gmail_message_ids(service):
    next_page_token = None
    while True:
        results = service.users().messages().list(
            userId='me',
            pageToken=next_page_token
        ).execute()
        for msg in results.get('messages', []):
            yield msg['id']
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    
#%%
def extract_email_data(service, msg_id):
    #limited date
    start_date, end_date = get_last_week_range()

    msg_data = service.users().messages().get(userId='me', id=msg_id).execute()
    headers = msg_data['payload'].get('headers', [])

    date_str = get_header(headers, 'Date')
    if not date_str:
        return None

    # Quick substring check to avoid full datetime parsing
    if not any(str(d) in date_str for d in [start_date, end_date]):
        try:
            email_date = parsedate_to_datetime(date_str).date()
        except Exception as e:
            print(f"Failed to parse date '{date_str}': {e}")
            return None
        if not (start_date <= email_date <= end_date):
            return None

    # Sender, title - metadata, source, addr - sender, parts, full-contnet - body 
    from_header = get_header(headers, 'From')
    title = get_header(headers, 'Subject')

    _, addr = parseaddr(from_header)
    addr = addr.lower().strip()
    source = DOMAIN_TO_COMPANY.get(addr, addr)

    snippet = msg_data.get('snippet', 'No snippet')

    parts = msg_data['payload'].get('parts', [])
    
    full_content = ''
    links = []

    for part in parts:
        mime_type = part.get('mimeType', '')
        body_data = part.get('body', {}).get('data')

        if not body_data:
            continue

        decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
        soup = BeautifulSoup(decoded, 'html.parser')
        full_content += soup.get_text(separator="\n") + "\n"
        
        #links
        if mime_type == 'text/html':
            for a_tag in soup.find_all('a', href=True):
                anchor_text = a_tag.get_text().strip().lower()
                href = a_tag['href'].strip()

                EXCLUDE_KEYWORDS = ['register', 'buy', 'purchase', 'shop', 'subscribe', 'sign up', 'donate', 'podcast', 'webinar', 'event']
                ARTICLE_HINTS = ['read', 'article', 'story', 'report']

                # Skip promotional links
                if any(kw in anchor_text for kw in EXCLUDE_KEYWORDS):
                    continue
                if any(kw in href.lower() for kw in EXCLUDE_KEYWORDS):
                    continue

                # Include only if anchor text suggests article-style content
                if any(hint in anchor_text for hint in ARTICLE_HINTS):
                    # Optional: unwrap Google redirect links
                    if href.startswith("https://www.google.com/url?q="):
                        href = unquote(href.split("q=")[-1].split("&")[0])
                    links.append(href)


    #sender_tags
    sender_tag_str = SOURCE_TAGS.get(source, 'Unlabeled')
    
    # summary
    # summary = summarize_text(clean_text(full_content))

    # tags- later
    # tags = []
    # if 'unsubscribe' in full_content.lower():
    #     tags.append('newsletter')
    # if 'invoice' in title.lower() or 'payment' in full_content.lower():
    #     tags.append('finance')
    # if not tags:
    #     tags.append('general')

    return {
    'date': email_date.strftime('%Y-%m-%d'),
    'source': source,
    'sender': from_header,
    'title': title,
    # 'tags': tags,
    'sender_tags': sender_tag_str,
    'links': links, 
    'snippet': snippet,
    'full_content': full_content,
    # 'summary': summary
    }

#%% 
def fetch_gmail_entries():
    service = get_gmail_service()
    entries = []

    for msg_id in get_gmail_message_ids(service):
        data = extract_email_data(service, msg_id)
        if data is None:
            continue
        entries.append({
            'Source': data['source'],
            'Title': data['title'],
            'Date': data['date'],
            'Link': data['links'] ,
            # 'Tags': ', '.join(data['tags']),
            'Sender Tags': data['sender_tags'],
            # 'Snippet': data['snippet'],
            # 'Summary': data['summary'],
            'Full_content': data['full_content']

        })
    return entries
#%%
def print_gmail_entries(entries):
    for entry in entries:
        print(f"Source       : {entry['Source']}")
        print(f"Title        : {entry['Title']}")
        print(f"Date         : {entry['Date']}")
        # print(f"Tags         : {entry['Tags']}")
        print(f"Sender Tags  : {entry['Sender Tags']}")
        print(f"Links        : {', '.join(entry['Link']) if isinstance(entry['Link'], list) else entry['Link']}")
        # print(f"Snippet      : {entry['Snippet']}")
        print(f"Full_content : {entry['Full_content']}")
        # print(f"Summary      : {entry['Summary']}")
        print('-' * 80)

# %% check 
# def main():
#     service = get_gmail_service()
#     entries = fetch_gmail_entries()
#     print(f"Total entries found: {len(entries)}") 
#     print_gmail_entries(entries)

# if __name__ == '__main__':
#     main()
# %%
