# RSS Feeds Configuration

> Documentation for RSS feed sources used by the newspaper publisher.

---

## Feed Regions

The publisher aggregates feeds from three regions:

| Region | File | Feed Count |
|--------|------|------------|
| INDIA | `rss_sites/india.py` | 55 feeds |
| USA | `rss_sites/usa.py` | ~30 feeds |
| GLOBAL | `rss_sites/global_news.py` | ~50 feeds |

---

## Feed Format

Each feed is a dictionary with the following structure:

```python
{
    'name': 'Times of India - India',
    'url': 'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',
    'category': 'India'
}
```

---

## India Feeds

Major sources include:

- **Times of India**: India, World, Tech, Sports, Entertainment
- **NDTV**: News, Business, Sports, Cricket
- **Hindustan Times**: Top News, India, World, Tech
- **The Hindu**: National, Business, Sports
- **Indian Express**: Top Stories, India, Business
- **Economic Times**: Markets, Tech
- **Mint**: News, Markets
- **News18**: Top Stories
- **Deccan Herald**: National
- **Tribune India**: Main News
- **And many more...**

---

## USA Feeds

Major sources include:

- **CNN**: Top Stories, World, Politics, Business
- **New York Times**: Home, World, US
- **Washington Post**: National, World
- **Fox News**: Latest, Politics
- **NPR**: News
- **USA Today**: Top Stories
- **And more...**

---

## Global Feeds

International sources include:

- **BBC**: World, Asia, Europe
- **Reuters**: Top News, World
- **Al Jazeera**: News, Features
- **France24**: World, Americas
- **DW (Deutsche Welle)**: Top Stories
- **The Guardian**: World
- **And more...**

---

## Adding Custom Feeds

### 1. Add to existing region file

```python
# In rss_sites/india.py

feeds = [
    # ... existing feeds ...
    
    {
        'name': 'My News Source',
        'url': 'https://example.com/rss',
        'category': 'Custom'
    }
]
```

### 2. Or use --url for single feed

```bash
python apps/newspaper_publisher/runner.py --url "https://example.com/rss" --style Classic --open
```

---

## Feed Troubleshooting

### Common Issues

1. **"Found 0 articles"**
   - Site may be blocking bots
   - RSS feed URL may be invalid
   - Feed may be empty

2. **Bot Protection**
   - The engine uses a browser-like User-Agent
   - Some sites still block automated requests
   - Usually ~60% of feeds return articles

3. **Image Issues**
   - Articles without images are discarded (`require_image=True`)
   - Images are resized to 600px max width
   - RGBA/palette images are converted to RGB

### Testing a Feed

```python
import feedparser
import requests

url = "https://example.com/rss"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

response = requests.get(url, headers=headers, timeout=10)
feed = feedparser.parse(response.content)

print(f"Entries: {len(feed.entries)}")
for entry in feed.entries[:3]:
    print(f"  - {entry.title}")
```
