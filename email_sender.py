#%%
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import base64
import re
from gmail_parser import get_gmail_service
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
def format_digest_as_html(digest):
    html = "<html><body>"
    html += "<h2>📰 Weekly Education Digest</h2>"

    for section in digest:
        html += f"<h3>🗂️ Group: {section['Group']}</h3>"

        summary = section['Summary']
        if summary == "Summary unavailable":
            html += "<p><strong>🧠 Summary unavailable. Showing combined text preview instead:</strong></p>"
            combined_text = "\n\n".join(
                clean_text(item.get('Content', '')) for item in section['Items'] if item.get('Content')
            )
            html += f"<p>{combined_text[:500]}...</p>"
        else:
            html += f"<p><strong>🧠 Summary:</strong> {summary}</p>"

        html += "<ul>"
        for item in section['Items']:
            title = item['Title']
            date = item['Date']
            source = item['Source']
            link = item.get('Link')

            html += "<li>"
            html += f"<strong>{title}</strong><br>"
            html += f"Date: {date}<br>"
            html += f"Source: {source}<br>"

            if isinstance(link, list) and link:
                html += "Links:<ul>"
                for l in link:
                    display_text = "View Article" if len(l) > 100 else l
                    html += f"<li><a href='{l}'>{display_text}</a></li>"
                html += "</ul>"
            elif isinstance(link, str) and link != 'N/A':
                display_text = "View Article" if len(link) > 100 else link
                html += f"Link: <a href='{link}'>{display_text}</a><br>"
            else:
                html += "Link: N/A<br>"

            html += "</li><br>"
        html += "</ul>"
        html += "<hr>"
    html += "</body></html>"
    return html

#%%
def create_message(sender, to, subject, html_content):
    message = MIMEText(html_content, "html")
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}
#%%
def send_message(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()
#%%
def send_digest_email(html_content):
    service = get_gmail_service()

    message = create_message("edtechnews.curator@gmail.com", "market.research@imaginelearning.com",  "Weekly Education Digest", html_content)
    response = send_message(service, "me", message)
    print("✅ Email sent. Message ID:", response['id'])
#%%