
from .india import feeds as india_feeds
from .usa import feeds as usa_feeds
from .global_news import feeds as global_feeds

ALL_FEEDS = {
    "india": india_feeds,
    "usa": usa_feeds,
    "global": global_feeds
}
