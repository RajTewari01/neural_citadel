"""
QR Studio - Data Handlers
=========================

Pure functions for formatting data into QR-encodable strings.
Each handler takes structured input and returns a properly formatted string.

Categories:
    - Web & URLs
    - Communication
    - Social Media
    - Finance & Payments
    - Contact Information
    - Location & Navigation
    - Media & Entertainment
    - Developer & Cloud
    - IoT & Smart Home
    - Authentication & Security
    - Documents & Files
    - Business & Enterprise
"""

import urllib.parse
from typing import Optional, Literal, Callable
from dataclasses import dataclass
from enum import Enum, auto


# =============================================================================
# ENUMS - QR DATA CATEGORIES
# =============================================================================

class QRCategory(Enum):
    """Top-level categories for QR data types."""
    WEB = auto()
    COMMUNICATION = auto()
    SOCIAL = auto()
    FINANCE = auto()
    CONTACT = auto()
    LOCATION = auto()
    CALENDAR = auto()
    WIFI = auto()
    MEDIA = auto()
    STORES = auto()
    DEVELOPER = auto()
    SECURITY = auto()
    IOT = auto()
    CONTENT = auto()
    REGIONAL_PAYMENT = auto()
    ASIAN_SOCIAL = auto()
    TRAVEL = auto()
    FOOD_DELIVERY = auto()
    DATING = auto()
    JOBS = auto()
    ECOMMERCE = auto()
    NFT_WEB3 = auto()
    PODCASTS = auto()
    NEWS = auto()
    GOVERNMENT = auto()
    EDUCATION = auto()
    HEALTHCARE = auto()
    TICKETING = auto()
    LOYALTY = auto()
    REAL_ESTATE = auto()


class WebType(Enum):
    """Web & URL QR types."""
    URL = "url"
    DEEP_LINK = "deep_link"
    UNIVERSAL_LINK = "universal_link"


class CommunicationType(Enum):
    """Communication QR types."""
    PHONE_CALL = "phone_call"
    SMS = "sms"
    MMS = "mms"
    EMAIL = "email"
    FACETIME = "facetime"
    WHATSAPP = "whatsapp"
    WHATSAPP_BUSINESS = "whatsapp_business"
    TELEGRAM_USER = "telegram_user"
    TELEGRAM_MESSAGE = "telegram_message"
    TELEGRAM_BOT = "telegram_bot"
    SIGNAL = "signal"
    VIBER = "viber"
    SKYPE_CALL = "skype_call"
    SKYPE_CHAT = "skype_chat"
    SKYPE_VIDEO = "skype_video"
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    TEAMS = "teams"
    DISCORD = "discord"
    SLACK_CHANNEL = "slack_channel"
    SLACK_INVITE = "slack_invite"
    THREEMA = "threema"
    SESSION = "session"
    MATRIX = "matrix"
    XMPP = "xmpp"


class SocialType(Enum):
    """Social media QR types."""
    INSTAGRAM_PROFILE = "instagram_profile"
    INSTAGRAM_POST = "instagram_post"
    FACEBOOK_PROFILE = "facebook_profile"
    FACEBOOK_EVENT = "facebook_event"
    FACEBOOK_GROUP = "facebook_group"
    TWITTER_PROFILE = "twitter_profile"
    TWITTER_TWEET = "twitter_tweet"
    TWITTER_COMPOSE = "twitter_compose"
    LINKEDIN_PROFILE = "linkedin_profile"
    LINKEDIN_COMPANY = "linkedin_company"
    LINKEDIN_SHARE = "linkedin_share"
    YOUTUBE_CHANNEL = "youtube_channel"
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    TIKTOK_PROFILE = "tiktok_profile"
    TIKTOK_VIDEO = "tiktok_video"
    SNAPCHAT_ADD = "snapchat_add"
    SNAPCHAT_LENS = "snapchat_lens"
    PINTEREST_PROFILE = "pinterest_profile"
    PINTEREST_BOARD = "pinterest_board"
    REDDIT_PROFILE = "reddit_profile"
    REDDIT_SUBREDDIT = "reddit_subreddit"
    REDDIT_POST = "reddit_post"
    TUMBLR = "tumblr"
    MASTODON = "mastodon"
    THREADS = "threads"
    BLUESKY = "bluesky"
    CLUBHOUSE = "clubhouse"
    BEREAL = "bereal"


class FinanceType(Enum):
    """Finance & payment QR types."""
    UPI = "upi"
    PAYTM = "paytm"
    PAYPAL = "paypal"
    VENMO = "venmo"
    CASH_APP = "cash_app"
    SEPA = "sepa"
    SWISS_QR = "swiss_qr"
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    ETHEREUM_TOKEN = "ethereum_token"
    USDT_ERC20 = "usdt_erc20"
    USDT_TRC20 = "usdt_trc20"
    LITECOIN = "litecoin"
    DOGECOIN = "dogecoin"
    MONERO = "monero"
    SOLANA = "solana"
    CARDANO = "cardano"
    RIPPLE = "ripple"
    BNB = "bnb"
    POLYGON = "polygon"


class ContactType(Enum):
    """Contact information QR types."""
    VCARD = "vcard"
    MECARD = "mecard"
    BIZCARD = "bizcard"


class LocationType(Enum):
    """Location & navigation QR types."""
    GEO = "geo"
    GOOGLE_MAPS_SEARCH = "google_maps_search"
    GOOGLE_MAPS_DIRECTIONS = "google_directions"
    GOOGLE_MAPS_PLACE = "google_maps_place"
    APPLE_MAPS_SEARCH = "apple_maps_search"
    APPLE_MAPS_DIRECTIONS = "apple_maps_directions"
    WAZE_NAVIGATE = "waze_navigate"
    WAZE_SEARCH = "waze_search"
    UBER = "uber"
    LYFT = "lyft"
    WHAT3WORDS = "what3words"
    PLUS_CODE = "plus_code"


class CalendarType(Enum):
    """Calendar & event QR types."""
    ICAL = "ical"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"


class WiFiType(Enum):
    """WiFi & network QR types."""
    WIFI = "wifi"
    WIFI_EAP = "wifi_eap"


class MediaType(Enum):
    """Media & entertainment QR types."""
    SPOTIFY_URI = "spotify_uri"
    SPOTIFY_TRACK = "spotify_track"
    SPOTIFY_PLAYLIST = "spotify_playlist"
    SPOTIFY_ARTIST = "spotify_artist"
    APPLE_MUSIC = "apple_music"
    APPLE_MUSIC_ALBUM = "apple_music_album"
    SOUNDCLOUD_USER = "soundcloud_user"
    SOUNDCLOUD_TRACK = "soundcloud_track"
    BANDCAMP = "bandcamp"
    DEEZER = "deezer"
    TIDAL = "tidal"
    TWITCH_CHANNEL = "twitch_channel"
    TWITCH_VOD = "twitch_vod"
    NETFLIX = "netflix"
    PRIME_VIDEO = "prime_video"
    IMDB = "imdb"
    STEAM_PROFILE = "steam_profile"
    STEAM_GAME = "steam_game"
    EPIC_GAMES = "epic_games"
    PLAYSTATION = "playstation"
    XBOX = "xbox"


class AppStoreType(Enum):
    """App store QR types."""
    GOOGLE_PLAY = "google_play"
    GOOGLE_PLAY_DEEP = "google_play_deep"
    APP_STORE = "app_store"
    APP_STORE_DEEP = "app_store_deep"
    AMAZON_APPSTORE = "amazon_appstore"
    HUAWEI_APPGALLERY = "huawei_appgallery"
    SAMSUNG_GALAXY = "samsung_galaxy"
    MICROSOFT_STORE = "microsoft_store"
    FDROID = "fdroid"


class DeveloperType(Enum):
    """Developer & cloud QR types."""
    GITHUB_PROFILE = "github_profile"
    GITHUB_REPO = "github_repo"
    GITHUB_GIST = "github_gist"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    NPM = "npm"
    PYPI = "pypi"
    DOCKER_HUB = "docker_hub"
    DROPBOX = "dropbox"
    GOOGLE_DRIVE_FILE = "google_drive_file"
    GOOGLE_DRIVE_FOLDER = "google_drive_folder"
    ONEDRIVE = "onedrive"
    NOTION = "notion"
    TRELLO = "trello"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    FIGMA = "figma"
    MIRO = "miro"


class SecurityType(Enum):
    """Authentication & security QR types."""
    TOTP = "totp"
    HOTP = "hotp"
    SSH = "ssh"
    SFTP = "sftp"
    WIREGUARD = "wireguard"
    SHADOWSOCKS = "shadowsocks"
    V2RAY = "v2ray"
    OPENVPN = "openvpn"


class IoTType(Enum):
    """IoT & smart home QR types."""
    HOME_ASSISTANT_WEBHOOK = "home_assistant_webhook"
    HOME_ASSISTANT_ENTITY = "home_assistant_entity"
    HOMEKIT = "homekit"
    MATTER = "matter"
    MQTT = "mqtt"
    ZIGBEE2MQTT = "zigbee2mqtt"
    IFTTT = "ifttt"
    IOS_SHORTCUT = "ios_shortcut"
    ANDROID_INTENT = "android_intent"
    TASKER = "tasker"


class ContentType(Enum):
    """Content & document QR types."""
    PDF = "pdf"
    ARXIV = "arxiv"
    DOI = "doi"
    ISBN = "isbn"
    WIKIPEDIA = "wikipedia"
    GOOGLE_SEARCH = "google_search"
    AMAZON_PRODUCT = "amazon_product"
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    BASE64 = "base64"


class RegionalPaymentType(Enum):
    """Regional payment system QR types."""
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    PIX = "pix"
    MPESA = "mpesa"
    GCASH = "gcash"
    PAYMAYA = "paymaya"
    GRABPAY = "grabpay"
    GOPAY = "gopay"
    OVO = "ovo"
    DANA = "dana"
    KAKAO_PAY = "kakao_pay"
    NAVER_PAY = "naver_pay"
    TOSS = "toss"
    LINE_PAY = "line_pay"
    RAKUTEN_PAY = "rakuten_pay"
    PAYPAY = "paypay"
    PROMPTPAY = "promptpay"
    TRUEMONEY = "truemoney"
    MOMO = "momo"
    ZALOPAY = "zalopay"
    VIETQR = "vietqr"
    TOUCH_N_GO = "touch_n_go"
    BOOST = "boost"
    PAYSERA = "paysera"
    REVOLUT = "revolut"
    WISE = "wise"
    KLARNA = "klarna"
    AFTERPAY = "afterpay"
    AFFIRM = "affirm"
    ZELLE = "zelle"


class AsianSocialType(Enum):
    """Asian social platform QR types."""
    WEIBO = "weibo"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    BILIBILI = "bilibili"
    QQ = "qq"
    WECHAT_PROFILE = "wechat_profile"
    VK = "vk"
    OK_RU = "ok_ru"
    LINE_PROFILE = "line_profile"
    LINE_ADD_FRIEND = "line_add_friend"
    KAKAOTALK = "kakaotalk"
    ZALO = "zalo"
    NAVER_BLOG = "naver_blog"
    MIXI = "mixi"
    BAIDU_TIEBA = "baidu_tieba"


class TravelType(Enum):
    """Travel & transportation QR types."""
    BOARDING_PASS = "boarding_pass"
    TRAIN_TICKET = "train_ticket"
    BUS_TICKET = "bus_ticket"
    BOOKING_COM = "booking_com"
    AIRBNB = "airbnb"
    TRIPADVISOR = "tripadvisor"
    OLA = "ola"
    GRAB = "grab"
    GOJEK = "gojek"
    DIDI = "didi"
    BOLT = "bolt"
    CABIFY = "cabify"
    LIME = "lime"
    BIRD = "bird"
    EV_CHARGING = "ev_charging"


class FoodDeliveryType(Enum):
    """Food delivery QR types."""
    UBER_EATS = "uber_eats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    POSTMATES = "postmates"
    DELIVEROO = "deliveroo"
    JUST_EAT = "just_eat"
    ZOMATO = "zomato"
    SWIGGY = "swiggy"
    FOODPANDA = "foodpanda"
    GRABFOOD = "grabfood"
    GOFOOD = "gofood"
    MEITUAN = "meituan"
    ELEME = "eleme"
    YELP = "yelp"
    OPENTABLE = "opentable"
    RESY = "resy"


class DatingType(Enum):
    """Dating app QR types."""
    TINDER = "tinder"
    BUMBLE = "bumble"
    HINGE = "hinge"
    OKCUPID = "okcupid"
    MATCH = "match"
    BADOO = "badoo"
    GRINDR = "grindr"
    HER = "her"


class JobsType(Enum):
    """Job platform QR types."""
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    MONSTER = "monster"
    ZIPRECRUITER = "ziprecruiter"
    UPWORK = "upwork"
    FIVERR = "fiverr"
    TOPTAL = "toptal"
    ANGELLIST = "angellist"
    HUNTR = "huntr"
    HANDSHAKE = "handshake"


class EcommerceType(Enum):
    """E-commerce QR types."""
    SHOPIFY = "shopify"
    ETSY = "etsy"
    EBAY = "ebay"
    ALIEXPRESS = "aliexpress"
    WISH = "wish"
    WALMART = "walmart"
    TARGET = "target"
    BESTBUY = "bestbuy"
    FLIPKART = "flipkart"
    LAZADA = "lazada"
    SHOPEE = "shopee"
    TOKOPEDIA = "tokopedia"
    TAOBAO = "taobao"
    JD = "jd"
    MERCARI = "mercari"
    POSHMARK = "poshmark"
    DEPOP = "depop"
    BARCODE = "barcode"


class NFTWeb3Type(Enum):
    """NFT & Web3 QR types."""
    OPENSEA = "opensea"
    RARIBLE = "rarible"
    FOUNDATION = "foundation"
    LOOKSRARE = "looksrare"
    METAMASK = "metamask"
    WALLETCONNECT = "walletconnect"
    ENS = "ens"
    IPFS = "ipfs"
    ARWEAVE = "arweave"
    ETHERSCAN_TX = "etherscan_tx"
    ETHERSCAN_ADDRESS = "etherscan_address"
    POLYGONSCAN = "polygonscan"
    BSCSCAN = "bscscan"
    SOLSCAN = "solscan"
    MAGIC_EDEN = "magic_eden"


class PodcastType(Enum):
    """Podcast QR types."""
    APPLE_PODCASTS = "apple_podcasts"
    GOOGLE_PODCASTS = "google_podcasts"
    SPOTIFY_PODCAST = "spotify_podcast"
    SPOTIFY_EPISODE = "spotify_episode"
    OVERCAST = "overcast"
    POCKET_CASTS = "pocket_casts"
    CASTBOX = "castbox"
    STITCHER = "stitcher"
    AUDIBLE = "audible"
    PODCAST_RSS = "podcast_rss"
    ANCHOR = "anchor"


class NewsType(Enum):
    """News & publication QR types."""
    MEDIUM = "medium"
    SUBSTACK = "substack"
    SUBSTACK_POST = "substack_post"
    MIRROR_XYZ = "mirror_xyz"
    HACKERNEWS = "hackernews"
    PRODUCTHUNT = "producthunt"
    NYTIMES = "nytimes"
    WSJ = "wsj"
    GUARDIAN = "guardian"
    BBC = "bbc"
    REUTERS = "reuters"


class GovernmentType(Enum):
    """Government & official QR types."""
    COVID_VACCINE = "covid_vaccine"
    EU_COVID_CERT = "eu_covid_cert"
    AADHAAR = "aadhaar"
    DIGILOCKER = "digilocker"
    MYGOV = "mygov"
    USCIS = "uscis"
    PASSPORT_MRZ = "passport_mrz"
    DRIVERS_LICENSE = "drivers_license"


class EducationType(Enum):
    """Education QR types."""
    COURSERA = "coursera"
    UDEMY = "udemy"
    EDX = "edx"
    KHAN_ACADEMY = "khan_academy"
    SKILLSHARE = "skillshare"
    LINKEDIN_LEARNING = "linkedin_learning"
    PLURALSIGHT = "pluralsight"
    CODECADEMY = "codecademy"
    DUOLINGO = "duolingo"
    QUIZLET = "quizlet"
    GOOGLE_CLASSROOM = "google_classroom"
    CANVAS = "canvas"
    STUDENT_ID = "student_id"


class HealthcareType(Enum):
    """Healthcare QR types."""
    MEDICAL_RECORD = "medical_record"
    PRESCRIPTION = "prescription"
    INSURANCE_CARD = "insurance_card"
    FHIR_PATIENT = "fhir_patient"
    APPLE_HEALTH = "apple_health"
    MYCHART = "mychart"


class TicketingType(Enum):
    """Ticketing & event QR types."""
    EVENTBRITE = "eventbrite"
    TICKETMASTER = "ticketmaster"
    STUBHUB = "stubhub"
    SEATGEEK = "seatgeek"
    MEETUP = "meetup"
    LUMA = "luma"
    MOVIE_TICKET = "movie_ticket"
    CONCERT_TICKET = "concert_ticket"
    SPORTS_TICKET = "sports_ticket"
    MUSEUM_TICKET = "museum_ticket"


class LoyaltyType(Enum):
    """Loyalty & membership QR types."""
    LOYALTY_CARD = "loyalty_card"
    GYM_MEMBERSHIP = "gym_membership"
    LIBRARY_CARD = "library_card"
    COSTCO = "costco"
    AMAZON_PRIME = "amazon_prime"
    FREQUENT_FLYER = "frequent_flyer"
    HOTEL_REWARDS = "hotel_rewards"


class RealEstateType(Enum):
    """Real estate QR types."""
    ZILLOW = "zillow"
    REALTOR = "realtor"
    REDFIN = "redfin"
    TRULIA = "trulia"
    APARTMENTS = "apartments"
    PROPERTY_QR = "property_qr"


# =============================================================================
# TYPE MAPPING - Enum to Handler Functions
# =============================================================================

@dataclass
class HandlerInfo:
    """Metadata for a handler function."""
    handler: Callable
    category: QRCategory
    description: str
    required_params: list
    optional_params: list = None


# =============================================================================
# HELPER UTILITIES
# =============================================================================

def _url_encode(text: str) -> str:
    """URL-encode a string for safe embedding."""
    return urllib.parse.quote(text, safe='')

def _ensure_https(url: str) -> str:
    """Ensure URL has https:// prefix."""
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    return url


# =============================================================================
# WEB & URLs
# =============================================================================

def format_url(url: str) -> str:
    """Basic URL/Website link."""
    return _ensure_https(url)

def format_deep_link(scheme: str, path: str, params: Optional[dict] = None) -> str:
    """Custom app deep link (e.g., myapp://page?id=123)."""
    base = f"{scheme}://{path}"
    if params:
        query = urllib.parse.urlencode(params)
        return f"{base}?{query}"
    return base

def format_universal_link(domain: str, path: str) -> str:
    """iOS/Android universal link."""
    return f"https://{domain}/{path.lstrip('/')}"


# =============================================================================
# COMMUNICATION
# =============================================================================

def format_phone_call(number: str) -> str:
    """Initiate phone call."""
    return f"tel:{number}"

def format_sms(number: str, message: str = "") -> str:
    """Send SMS message."""
    if message:
        return f"SMSTO:{number}:{message}"
    return f"SMSTO:{number}"

def format_mms(number: str, message: str = "", subject: str = "") -> str:
    """Send MMS message."""
    base = f"mmsto:{number}"
    params = {}
    if message:
        params['body'] = message
    if subject:
        params['subject'] = subject
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_email(
    to: str,
    subject: str = "",
    body: str = "",
    cc: str = "",
    bcc: str = ""
) -> str:
    """Compose email."""
    params = {}
    if subject:
        params['subject'] = subject
    if body:
        params['body'] = body
    if cc:
        params['cc'] = cc
    if bcc:
        params['bcc'] = bcc
    
    if params:
        return f"mailto:{to}?{urllib.parse.urlencode(params)}"
    return f"mailto:{to}"

def format_facetime(identifier: str, audio_only: bool = False) -> str:
    """FaceTime call (Apple)."""
    scheme = "facetime-audio" if audio_only else "facetime"
    return f"{scheme}:{identifier}"

def format_whatsapp(phone: str, message: str = "") -> str:
    """WhatsApp message. Phone should include country code without +."""
    phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    if message:
        return f"https://wa.me/{phone}?text={_url_encode(message)}"
    return f"https://wa.me/{phone}"

def format_whatsapp_business(phone: str, message: str = "") -> str:
    """WhatsApp Business catalog link."""
    return format_whatsapp(phone, message)

def format_telegram_user(username: str) -> str:
    """Telegram user/channel link."""
    return f"https://t.me/{username.lstrip('@')}"

def format_telegram_message(username: str, message: str) -> str:
    """Telegram with pre-filled message."""
    return f"https://t.me/{username.lstrip('@')}?text={_url_encode(message)}"

def format_telegram_bot(bot_username: str, start_param: str = "") -> str:
    """Telegram bot deep link."""
    base = f"https://t.me/{bot_username}"
    if start_param:
        return f"{base}?start={start_param}"
    return base

def format_signal(phone: str) -> str:
    """Signal Messenger link. Phone with country code."""
    return f"https://signal.me/#p/{phone}"

def format_viber(phone: str) -> str:
    """Viber chat link."""
    return f"viber://chat?number={phone}"

def format_skype_call(username: str) -> str:
    """Skype voice call."""
    return f"skype:{username}?call"

def format_skype_chat(username: str) -> str:
    """Skype text chat."""
    return f"skype:{username}?chat"

def format_skype_video(username: str) -> str:
    """Skype video call."""
    return f"skype:{username}?call&video=true"

def format_zoom_meeting(meeting_id: str, passcode: str = "") -> str:
    """Zoom meeting join link."""
    base = f"https://zoom.us/j/{meeting_id}"
    if passcode:
        return f"{base}?pwd={passcode}"
    return base

def format_google_meet(meeting_code: str) -> str:
    """Google Meet link."""
    if meeting_code.startswith('http'):
        return meeting_code
    return f"https://meet.google.com/{meeting_code}"

def format_microsoft_teams(
    meeting_url: str = "",
    tenant_id: str = "",
    thread_id: str = ""
) -> str:
    """Microsoft Teams meeting or deep link."""
    if meeting_url:
        return meeting_url
    if tenant_id and thread_id:
        return f"https://teams.microsoft.com/l/meetup-join/{tenant_id}/{thread_id}"
    return "https://teams.microsoft.com"

def format_discord_invite(invite_code: str) -> str:
    """Discord server invite."""
    if invite_code.startswith('http'):
        return invite_code
    return f"https://discord.gg/{invite_code}"

def format_slack_channel(workspace: str, channel: str) -> str:
    """Slack channel deep link."""
    return f"slack://channel?team={workspace}&id={channel}"

def format_slack_invite(invite_url: str) -> str:
    """Slack workspace invite."""
    return invite_url

def format_threema_id(threema_id: str) -> str:
    """Threema (encrypted messenger) contact."""
    return f"threema://add?id={threema_id}"

def format_session_id(session_id: str) -> str:
    """Session messenger (privacy-focused)."""
    return f"https://getsession.org/users/{session_id}"

def format_matrix_user(user_id: str) -> str:
    """Matrix/Element user link."""
    return f"https://matrix.to/#/{user_id}"

def format_xmpp(jabber_id: str) -> str:
    """XMPP/Jabber contact."""
    return f"xmpp:{jabber_id}"


# =============================================================================
# SOCIAL MEDIA
# =============================================================================

def format_instagram_profile(username: str) -> str:
    """Instagram profile."""
    return f"https://instagram.com/{username.lstrip('@')}"

def format_instagram_post(shortcode: str) -> str:
    """Instagram specific post."""
    return f"https://instagram.com/p/{shortcode}"

def format_facebook_profile(username: str) -> str:
    """Facebook profile/page."""
    return f"https://facebook.com/{username}"

def format_facebook_event(event_id: str) -> str:
    """Facebook event."""
    return f"https://facebook.com/events/{event_id}"

def format_facebook_group(group_id: str) -> str:
    """Facebook group."""
    return f"https://facebook.com/groups/{group_id}"

def format_twitter_profile(username: str) -> str:
    """X (Twitter) profile."""
    return f"https://twitter.com/{username.lstrip('@')}"

def format_twitter_tweet(tweet_id: str) -> str:
    """X (Twitter) specific tweet."""
    return f"https://twitter.com/i/status/{tweet_id}"

def format_twitter_compose(text: str, url: str = "", hashtags: str = "") -> str:
    """X (Twitter) compose tweet intent."""
    params = {'text': text}
    if url:
        params['url'] = url
    if hashtags:
        params['hashtags'] = hashtags
    return f"https://twitter.com/intent/tweet?{urllib.parse.urlencode(params)}"

def format_linkedin_profile(username: str) -> str:
    """LinkedIn profile."""
    return f"https://linkedin.com/in/{username}"

def format_linkedin_company(company: str) -> str:
    """LinkedIn company page."""
    return f"https://linkedin.com/company/{company}"

def format_linkedin_share(url: str) -> str:
    """LinkedIn share intent."""
    return f"https://www.linkedin.com/sharing/share-offsite/?url={_url_encode(url)}"

def format_youtube_channel(handle: str) -> str:
    """YouTube channel."""
    if handle.startswith('@'):
        return f"https://youtube.com/{handle}"
    return f"https://youtube.com/@{handle}"

def format_youtube_video(video_id: str, timestamp: int = 0) -> str:
    """YouTube video with optional timestamp."""
    base = f"https://youtu.be/{video_id}"
    if timestamp:
        return f"{base}?t={timestamp}"
    return base

def format_youtube_playlist(playlist_id: str) -> str:
    """YouTube playlist."""
    return f"https://youtube.com/playlist?list={playlist_id}"

def format_tiktok_profile(username: str) -> str:
    """TikTok profile."""
    return f"https://tiktok.com/@{username.lstrip('@')}"

def format_tiktok_video(video_id: str) -> str:
    """TikTok specific video."""
    return f"https://vm.tiktok.com/{video_id}"

def format_snapchat_add(username: str) -> str:
    """Snapchat add friend."""
    return f"https://snapchat.com/add/{username}"

def format_snapchat_lens(lens_id: str) -> str:
    """Snapchat lens link."""
    return f"https://snapchat.com/unlock/?type=SNAPCODE&uuid={lens_id}"

def format_pinterest_profile(username: str) -> str:
    """Pinterest profile."""
    return f"https://pinterest.com/{username}"

def format_pinterest_board(username: str, board: str) -> str:
    """Pinterest board."""
    return f"https://pinterest.com/{username}/{board}"

def format_reddit_profile(username: str) -> str:
    """Reddit user profile."""
    return f"https://reddit.com/user/{username}"

def format_reddit_subreddit(subreddit: str) -> str:
    """Reddit subreddit."""
    return f"https://reddit.com/r/{subreddit.lstrip('r/')}"

def format_reddit_post(subreddit: str, post_id: str) -> str:
    """Reddit specific post."""
    return f"https://reddit.com/r/{subreddit}/comments/{post_id}"

def format_tumblr_blog(blog_name: str) -> str:
    """Tumblr blog."""
    return f"https://{blog_name}.tumblr.com"

def format_mastodon_profile(username: str, instance: str = "mastodon.social") -> str:
    """Mastodon/Fediverse profile."""
    return f"https://{instance}/@{username.lstrip('@')}"

def format_threads_profile(username: str) -> str:
    """Threads (Meta) profile."""
    return f"https://threads.net/@{username.lstrip('@')}"

def format_bluesky_profile(handle: str) -> str:
    """Bluesky profile."""
    return f"https://bsky.app/profile/{handle}"

def format_clubhouse_profile(username: str) -> str:
    """Clubhouse profile."""
    return f"https://joinclubhouse.com/@{username}"

def format_bereal_profile(username: str) -> str:
    """BeReal profile."""
    return f"https://bfrnd.com/{username}"


# =============================================================================
# FINANCE & PAYMENTS
# =============================================================================

def format_upi(
    upi_id: str,
    payee_name: str,
    amount: str = "",
    transaction_note: str = "",
    currency: str = "INR"
) -> str:
    """UPI Payment (India)."""
    params = {
        'pa': upi_id,
        'pn': payee_name,
        'cu': currency
    }
    if amount:
        params['am'] = amount
    if transaction_note:
        params['tn'] = transaction_note
    return f"upi://pay?{urllib.parse.urlencode(params)}"

def format_paytm(
    phone: str = "",
    upi_id: str = "",
    amount: str = "",
    note: str = ""
) -> str:
    """Paytm payment link (India)."""
    params = {}
    if phone:
        params['phone'] = phone
    if upi_id:
        params['pa'] = upi_id
    if amount:
        params['am'] = amount
    if note:
        params['tn'] = note
    return f"paytmmp://pay?{urllib.parse.urlencode(params)}"

def format_paypal(username: str, amount: str = "", currency: str = "USD") -> str:
    """PayPal.me link."""
    base = f"https://paypal.me/{username}"
    if amount:
        return f"{base}/{amount}{currency}"
    return base

def format_venmo(username: str, amount: str = "", note: str = "") -> str:
    """Venmo payment."""
    params = {}
    if amount:
        params['amount'] = amount
    if note:
        params['note'] = note
    base = f"venmo://paycharge?txn=pay&recipients={username}"
    if params:
        return f"{base}&{urllib.parse.urlencode(params)}"
    return base

def format_cash_app(cashtag: str, amount: str = "") -> str:
    """Cash App payment."""
    base = f"https://cash.app/${cashtag.lstrip('$')}"
    if amount:
        return f"{base}/{amount}"
    return base

def format_sepa_transfer(
    bic: str,
    iban: str,
    recipient_name: str,
    amount: str,
    reference: str = ""
) -> str:
    """SEPA bank transfer (EU). EPC QR format."""
    lines = [
        "BCD",
        "002",
        "1",
        "SCT",
        bic,
        recipient_name,
        iban,
        f"EUR{amount}",
        "",
        reference,
        ""
    ]
    return "\n".join(lines)

def format_swiss_qr_bill(
    iban: str,
    amount: str,
    creditor_name: str,
    creditor_address: str,
    reference: str = ""
) -> str:
    """Swiss QR-Bill format."""
    # Simplified version - full spec has 31 fields
    lines = [
        "SPC",
        "0200",
        "1",
        iban,
        "K",
        creditor_name,
        creditor_address,
        "", "", "",
        amount,
        "CHF",
        "", "", "", "", "",
        "NON",
        reference
    ]
    return "\n".join(lines)

# Cryptocurrency Handlers
def format_bitcoin(address: str, amount: str = "", label: str = "", message: str = "") -> str:
    """Bitcoin payment."""
    params = {}
    if amount:
        params['amount'] = amount
    if label:
        params['label'] = label
    if message:
        params['message'] = message
    base = f"bitcoin:{address}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_ethereum(address: str, value: str = "", gas: str = "", data: str = "") -> str:
    """Ethereum payment (EIP-681)."""
    params = {}
    if value:
        params['value'] = value
    if gas:
        params['gas'] = gas
    if data:
        params['data'] = data
    base = f"ethereum:{address}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_ethereum_token(
    token_address: str,
    recipient: str,
    amount: str,
    chain_id: int = 1
) -> str:
    """ERC-20 token transfer."""
    return f"ethereum:{token_address}@{chain_id}/transfer?address={recipient}&uint256={amount}"

def format_usdt_erc20(address: str, amount: str = "") -> str:
    """USDT on Ethereum."""
    return format_ethereum(address, amount)

def format_usdt_trc20(address: str) -> str:
    """USDT on Tron."""
    return f"tron:{address}"

def format_litecoin(address: str, amount: str = "", label: str = "") -> str:
    """Litecoin payment."""
    params = {}
    if amount:
        params['amount'] = amount
    if label:
        params['label'] = label
    base = f"litecoin:{address}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_dogecoin(address: str, amount: str = "") -> str:
    """Dogecoin payment."""
    if amount:
        return f"dogecoin:{address}?amount={amount}"
    return f"dogecoin:{address}"

def format_monero(address: str, amount: str = "", payment_id: str = "") -> str:
    """Monero (XMR) payment."""
    params = {}
    if amount:
        params['tx_amount'] = amount
    if payment_id:
        params['tx_payment_id'] = payment_id
    base = f"monero:{address}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_solana(address: str, amount: str = "", reference: str = "") -> str:
    """Solana payment."""
    params = {}
    if amount:
        params['amount'] = amount
    if reference:
        params['reference'] = reference
    base = f"solana:{address}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_cardano(address: str, amount: str = "") -> str:
    """Cardano (ADA) payment."""
    if amount:
        return f"web+cardano:{address}?amount={amount}"
    return f"web+cardano:{address}"

def format_ripple(address: str, amount: str = "", dt: str = "") -> str:
    """Ripple (XRP) payment."""
    params = {}
    if amount:
        params['amount'] = amount
    if dt:
        params['dt'] = dt  # Destination tag
    base = f"ripple:{address}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_bnb(address: str, amount: str = "") -> str:
    """Binance Coin."""
    if amount:
        return f"bnb:{address}?amount={amount}"
    return f"bnb:{address}"

def format_polygon_matic(address: str, amount: str = "") -> str:
    """Polygon/MATIC."""
    if amount:
        return f"ethereum:{address}@137?value={amount}"
    return f"ethereum:{address}@137"


# =============================================================================
# CONTACT INFORMATION
# =============================================================================

def format_vcard(
    name: str,
    phone: str = "",
    email: str = "",
    organization: str = "",
    title: str = "",
    website: str = "",
    address: str = "",
    birthday: str = "",
    note: str = "",
    photo_url: str = ""
) -> str:
    """vCard 3.0 format - Full contact card."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{name}",
    ]
    
    if organization:
        lines.append(f"ORG:{organization}")
    if title:
        lines.append(f"TITLE:{title}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{phone}")
    if email:
        lines.append(f"EMAIL:{email}")
    if website:
        lines.append(f"URL:{website}")
    if address:
        lines.append(f"ADR;TYPE=WORK:;;{address};;;;")
    if birthday:
        lines.append(f"BDAY:{birthday}")
    if note:
        lines.append(f"NOTE:{note}")
    if photo_url:
        lines.append(f"PHOTO;VALUE=URI:{photo_url}")
    
    lines.append("END:VCARD")
    return "\n".join(lines)

def format_mecard(name: str, phone: str = "", email: str = "", address: str = "") -> str:
    """MeCard format - Simpler contact card."""
    parts = [f"MECARD:N:{name}"]
    if phone:
        parts.append(f"TEL:{phone}")
    if email:
        parts.append(f"EMAIL:{email}")
    if address:
        parts.append(f"ADR:{address}")
    return ";".join(parts) + ";;"

def format_bizcard(
    name: str,
    company: str = "",
    title: str = "",
    phone: str = "",
    email: str = "",
    address: str = ""
) -> str:
    """BIZCARD format."""
    parts = ["BIZCARD:"]
    if name:
        parts.append(f"N:{name};")
    if company:
        parts.append(f"C:{company};")
    if title:
        parts.append(f"T:{title};")
    if phone:
        parts.append(f"P:{phone};")
    if email:
        parts.append(f"E:{email};")
    if address:
        parts.append(f"A:{address};")
    return "".join(parts)


# =============================================================================
# LOCATION & NAVIGATION
# =============================================================================

def format_geo_coordinates(latitude: float, longitude: float, altitude: float = None) -> str:
    """Geo URI (RFC 5870)."""
    if altitude:
        return f"geo:{latitude},{longitude},{altitude}"
    return f"geo:{latitude},{longitude}"

def format_google_maps_search(query: str) -> str:
    """Google Maps search."""
    return f"https://www.google.com/maps/search/?api=1&query={_url_encode(query)}"

def format_google_maps_directions(
    destination: str,
    origin: str = "",
    mode: Literal["driving", "walking", "bicycling", "transit"] = "driving"
) -> str:
    """Google Maps directions."""
    params = {
        'api': '1',
        'destination': destination,
        'travelmode': mode
    }
    if origin:
        params['origin'] = origin
    return f"https://www.google.com/maps/dir/?{urllib.parse.urlencode(params)}"

def format_google_maps_place(place_id: str) -> str:
    """Google Maps place by ID."""
    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"

def format_apple_maps_search(query: str) -> str:
    """Apple Maps search."""
    return f"https://maps.apple.com/?q={_url_encode(query)}"

def format_apple_maps_directions(
    destination: str,
    destination_lat: float = None,
    destination_lon: float = None
) -> str:
    """Apple Maps directions."""
    if destination_lat and destination_lon:
        return f"https://maps.apple.com/?daddr={destination_lat},{destination_lon}"
    return f"https://maps.apple.com/?daddr={_url_encode(destination)}"

def format_waze_navigate(latitude: float, longitude: float) -> str:
    """Waze navigation."""
    return f"waze://?ll={latitude},{longitude}&navigate=yes"

def format_waze_search(query: str) -> str:
    """Waze search."""
    return f"waze://?q={_url_encode(query)}"

def format_uber_ride(
    pickup_lat: float = None,
    pickup_lon: float = None,
    dropoff_lat: float = None,
    dropoff_lon: float = None,
    dropoff_address: str = ""
) -> str:
    """Uber ride request."""
    params = {'action': 'setPickup'}
    if pickup_lat and pickup_lon:
        params['pickup[latitude]'] = pickup_lat
        params['pickup[longitude]'] = pickup_lon
    if dropoff_lat and dropoff_lon:
        params['dropoff[latitude]'] = dropoff_lat
        params['dropoff[longitude]'] = dropoff_lon
    elif dropoff_address:
        params['dropoff[formatted_address]'] = dropoff_address
    return f"uber://?{urllib.parse.urlencode(params)}"

def format_lyft_ride(destination_lat: float, destination_lon: float) -> str:
    """Lyft ride request."""
    return f"lyft://ridetype?id=lyft&destination[latitude]={destination_lat}&destination[longitude]={destination_lon}"

def format_what3words(words: str) -> str:
    """What3Words location."""
    return f"https://what3words.com/{words}"

def format_plus_code(code: str) -> str:
    """Google Plus Code."""
    return f"https://plus.codes/{code}"


# =============================================================================
# CALENDAR & EVENTS
# =============================================================================

def format_ical_event(
    title: str,
    start: str,  # YYYYMMDDTHHMMSSZ
    end: str,    # YYYYMMDDTHHMMSSZ
    description: str = "",
    location: str = "",
    url: str = ""
) -> str:
    """iCalendar event (VEVENT)."""
    lines = [
        "BEGIN:VEVENT",
        f"SUMMARY:{title}",
        f"DTSTART:{start}",
        f"DTEND:{end}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{description}")
    if location:
        lines.append(f"LOCATION:{location}")
    if url:
        lines.append(f"URL:{url}")
    lines.append("END:VEVENT")
    return "\n".join(lines)

def format_google_calendar_event(
    title: str,
    start: str,  # YYYYMMDDTHHMMSS
    end: str,
    description: str = "",
    location: str = ""
) -> str:
    """Google Calendar add event link."""
    params = {
        'action': 'TEMPLATE',
        'text': title,
        'dates': f"{start}/{end}"
    }
    if description:
        params['details'] = description
    if location:
        params['location'] = location
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def format_outlook_calendar_event(
    title: str,
    start: str,
    end: str,
    body: str = "",
    location: str = ""
) -> str:
    """Outlook calendar add event."""
    params = {
        'path': '/calendar/action/compose',
        'rru': 'addevent',
        'subject': title,
        'startdt': start,
        'enddt': end
    }
    if body:
        params['body'] = body
    if location:
        params['location'] = location
    return f"https://outlook.live.com/calendar/0/deeplink/compose?{urllib.parse.urlencode(params)}"


# =============================================================================
# WIFI & NETWORK
# =============================================================================

def format_wifi(
    ssid: str,
    password: str = "",
    encryption: Literal["WPA", "WPA2", "WPA3", "WEP", "nopass"] = "WPA",
    hidden: bool = False
) -> str:
    """WiFi network configuration."""
    hidden_str = "true" if hidden else "false"
    if encryption == "nopass":
        return f"WIFI:S:{ssid};T:nopass;H:{hidden_str};;"
    return f"WIFI:S:{ssid};T:{encryption};P:{password};H:{hidden_str};;"

def format_wifi_eap(
    ssid: str,
    eap_method: str,
    identity: str,
    password: str = "",
    anonymous_identity: str = "",
    phase2: str = ""
) -> str:
    """Enterprise WiFi (EAP)."""
    base = f"WIFI:S:{ssid};T:WPA2-EAP;E:{eap_method};I:{identity};"
    if password:
        base += f"P:{password};"
    if anonymous_identity:
        base += f"A:{anonymous_identity};"
    if phase2:
        base += f"PH2:{phase2};"
    return base + ";"


# =============================================================================
# MEDIA & ENTERTAINMENT
# =============================================================================

def format_spotify_uri(uri: str) -> str:
    """Spotify URI (track, album, playlist, artist)."""
    if uri.startswith('spotify:'):
        return uri
    if 'open.spotify.com' in uri:
        return uri
    return f"spotify:{uri}"

def format_spotify_track(track_id: str) -> str:
    """Spotify track."""
    return f"https://open.spotify.com/track/{track_id}"

def format_spotify_playlist(playlist_id: str) -> str:
    """Spotify playlist."""
    return f"https://open.spotify.com/playlist/{playlist_id}"

def format_spotify_artist(artist_id: str) -> str:
    """Spotify artist."""
    return f"https://open.spotify.com/artist/{artist_id}"

def format_apple_music_url(url: str) -> str:
    """Apple Music link."""
    return url

def format_apple_music_album(album_id: str, country: str = "us") -> str:
    """Apple Music album."""
    return f"https://music.apple.com/{country}/album/{album_id}"

def format_soundcloud_user(username: str) -> str:
    """SoundCloud profile."""
    return f"https://soundcloud.com/{username}"

def format_soundcloud_track(user: str, track: str) -> str:
    """SoundCloud specific track."""
    return f"https://soundcloud.com/{user}/{track}"

def format_bandcamp_artist(artist: str) -> str:
    """Bandcamp artist page."""
    return f"https://{artist}.bandcamp.com"

def format_deezer_track(track_id: str) -> str:
    """Deezer track."""
    return f"https://www.deezer.com/track/{track_id}"

def format_tidal_url(url: str) -> str:
    """Tidal link."""
    return url

def format_twitch_channel(username: str) -> str:
    """Twitch channel."""
    return f"https://twitch.tv/{username}"

def format_twitch_vod(video_id: str) -> str:
    """Twitch VOD."""
    return f"https://twitch.tv/videos/{video_id}"

def format_netflix_title(title_id: str) -> str:
    """Netflix title."""
    return f"https://www.netflix.com/title/{title_id}"

def format_primevideo_title(title_id: str) -> str:
    """Amazon Prime Video."""
    return f"https://www.amazon.com/dp/{title_id}"

def format_imdb_title(title_id: str) -> str:
    """IMDb title/movie."""
    return f"https://www.imdb.com/title/{title_id}"

def format_steam_profile(steam_id: str) -> str:
    """Steam profile."""
    return f"https://steamcommunity.com/id/{steam_id}"

def format_steam_game(app_id: str) -> str:
    """Steam game store page."""
    return f"https://store.steampowered.com/app/{app_id}"

def format_epic_games(game_slug: str) -> str:
    """Epic Games Store game."""
    return f"https://store.epicgames.com/p/{game_slug}"

def format_playstation_profile(username: str) -> str:
    """PlayStation Network profile."""
    return f"https://psnprofiles.com/{username}"

def format_xbox_profile(gamertag: str) -> str:
    """Xbox profile."""
    return f"https://account.xbox.com/profile?gamertag={gamertag}"


# =============================================================================
# APP STORES
# =============================================================================

def format_google_play_app(package_name: str) -> str:
    """Google Play Store app."""
    return f"https://play.google.com/store/apps/details?id={package_name}"

def format_google_play_deep(package_name: str) -> str:
    """Google Play Store deep link (opens app directly)."""
    return f"market://details?id={package_name}"

def format_apple_app_store(app_id: str, country: str = "us") -> str:
    """Apple App Store."""
    return f"https://apps.apple.com/{country}/app/id{app_id}"

def format_apple_app_store_deep(app_id: str) -> str:
    """Apple App Store deep link."""
    return f"itms-apps://itunes.apple.com/app/id{app_id}"

def format_amazon_appstore(asin: str) -> str:
    """Amazon Appstore."""
    return f"https://www.amazon.com/dp/{asin}"

def format_huawei_appgallery(app_id: str) -> str:
    """Huawei AppGallery."""
    return f"appmarket://details?id={app_id}"

def format_samsung_galaxy_store(app_id: str) -> str:
    """Samsung Galaxy Store."""
    return f"samsungapps://ProductDetail/{app_id}"

def format_microsoft_store(product_id: str) -> str:
    """Microsoft Store."""
    return f"ms-windows-store://pdp/?productid={product_id}"

def format_fdroid_app(package_name: str) -> str:
    """F-Droid (open source apps)."""
    return f"https://f-droid.org/packages/{package_name}"


# =============================================================================
# DEVELOPER & CLOUD
# =============================================================================

def format_github_profile(username: str) -> str:
    """GitHub user profile."""
    return f"https://github.com/{username}"

def format_github_repo(owner: str, repo: str) -> str:
    """GitHub repository."""
    return f"https://github.com/{owner}/{repo}"

def format_github_gist(gist_id: str) -> str:
    """GitHub Gist."""
    return f"https://gist.github.com/{gist_id}"

def format_gitlab_project(namespace: str, project: str) -> str:
    """GitLab project."""
    return f"https://gitlab.com/{namespace}/{project}"

def format_bitbucket_repo(workspace: str, repo: str) -> str:
    """Bitbucket repository."""
    return f"https://bitbucket.org/{workspace}/{repo}"

def format_npm_package(package_name: str) -> str:
    """NPM package."""
    return f"https://www.npmjs.com/package/{package_name}"

def format_pypi_package(package_name: str) -> str:
    """PyPI package."""
    return f"https://pypi.org/project/{package_name}"

def format_docker_hub(image: str) -> str:
    """Docker Hub image."""
    return f"https://hub.docker.com/r/{image}"

def format_dropbox_link(link: str) -> str:
    """Dropbox shared link."""
    return link

def format_google_drive_file(file_id: str) -> str:
    """Google Drive file."""
    return f"https://drive.google.com/file/d/{file_id}/view"

def format_google_drive_folder(folder_id: str) -> str:
    """Google Drive folder."""
    return f"https://drive.google.com/drive/folders/{folder_id}"

def format_onedrive_link(link: str) -> str:
    """OneDrive shared link."""
    return link

def format_notion_page(page_id: str) -> str:
    """Notion page."""
    return f"https://notion.so/{page_id}"

def format_trello_board(board_id: str) -> str:
    """Trello board."""
    return f"https://trello.com/b/{board_id}"

def format_jira_issue(domain: str, issue_key: str) -> str:
    """Jira issue."""
    return f"https://{domain}/browse/{issue_key}"

def format_confluence_page(domain: str, page_id: str) -> str:
    """Confluence page."""
    return f"https://{domain}/wiki/spaces/viewpage.action?pageId={page_id}"

def format_figma_file(file_key: str) -> str:
    """Figma file."""
    return f"https://www.figma.com/file/{file_key}"

def format_miro_board(board_id: str) -> str:
    """Miro board."""
    return f"https://miro.com/app/board/{board_id}"


# =============================================================================
# AUTHENTICATION & SECURITY
# =============================================================================

def format_totp(
    secret: str,
    account_name: str,
    issuer: str,
    algorithm: str = "SHA1",
    digits: int = 6,
    period: int = 30
) -> str:
    """TOTP 2FA setup (Google Authenticator, Authy, etc.)."""
    label = f"{issuer}:{account_name}"
    params = {
        'secret': secret,
        'issuer': issuer,
        'algorithm': algorithm,
        'digits': digits,
        'period': period
    }
    return f"otpauth://totp/{_url_encode(label)}?{urllib.parse.urlencode(params)}"

def format_hotp(
    secret: str,
    account_name: str,
    issuer: str,
    counter: int,
    digits: int = 6
) -> str:
    """HOTP 2FA setup."""
    label = f"{issuer}:{account_name}"
    params = {
        'secret': secret,
        'issuer': issuer,
        'counter': counter,
        'digits': digits
    }
    return f"otpauth://hotp/{_url_encode(label)}?{urllib.parse.urlencode(params)}"

def format_ssh_connection(user: str, host: str, port: int = 22) -> str:
    """SSH connection string."""
    if port != 22:
        return f"ssh://{user}@{host}:{port}"
    return f"ssh://{user}@{host}"

def format_sftp_connection(user: str, host: str, port: int = 22) -> str:
    """SFTP connection string."""
    if port != 22:
        return f"sftp://{user}@{host}:{port}"
    return f"sftp://{user}@{host}"

def format_wireguard_config(config_data: str) -> str:
    """WireGuard VPN config (Base64 encoded)."""
    import base64
    encoded = base64.b64encode(config_data.encode()).decode()
    return f"wireguard://{encoded}"

def format_shadowsocks(config_base64: str) -> str:
    """ShadowSocks VPN config."""
    return f"ss://{config_base64}"

def format_v2ray(config_base64: str) -> str:
    """V2Ray/Xray config."""
    return f"vmess://{config_base64}"

def format_openvpn_import(config_url: str) -> str:
    """OpenVPN config import."""
    return f"openvpn://import-profile/{config_url}"


# =============================================================================
# IOT & SMART HOME
# =============================================================================

def format_home_assistant_webhook(webhook_id: str, domain: str = "homeassistant.local") -> str:
    """Home Assistant webhook trigger."""
    return f"https://{domain}/api/webhook/{webhook_id}"

def format_home_assistant_entity(entity_id: str) -> str:
    """Home Assistant entity deep link."""
    return f"homeassistant://navigate/entities/{entity_id}"

def format_homekit_setup_code(setup_code: str) -> str:
    """Apple HomeKit setup code."""
    return f"X-HM://{setup_code}"

def format_matter_setup(setup_code: str) -> str:
    """Matter/Thread device setup."""
    return f"MT:{setup_code}"

def format_mqtt_topic(broker: str, topic: str, port: int = 1883) -> str:
    """MQTT broker connection."""
    return f"mqtt://{broker}:{port}/{topic}"

def format_zigbee2mqtt_device(device_id: str) -> str:
    """Zigbee2MQTT device link."""
    return f"z2m://{device_id}"

def format_ifttt_webhook(event_name: str, key: str) -> str:
    """IFTTT webhook trigger."""
    return f"https://maker.ifttt.com/trigger/{event_name}/with/key/{key}"

def format_ios_shortcut(shortcut_name: str, input_text: str = "") -> str:
    """iOS Shortcuts app."""
    base = f"shortcuts://run-shortcut?name={_url_encode(shortcut_name)}"
    if input_text:
        return f"{base}&input=text&text={_url_encode(input_text)}"
    return base

def format_android_intent(
    action: str,
    package: str = "",
    component: str = "",
    extras: dict = None
) -> str:
    """Android Intent URL."""
    base = f"intent://#Intent;action={action};"
    if package:
        base += f"package={package};"
    if component:
        base += f"component={component};"
    if extras:
        for key, value in extras.items():
            base += f"S.{key}={value};"
    return base + "end"

def format_tasker_task(task_name: str) -> str:
    """Tasker (Android automation) task."""
    return f"tasker://perform_task?name={task_name}"


# =============================================================================
# DOCUMENTS & CONTENT
# =============================================================================

def format_pdf_url(url: str) -> str:
    """PDF document link."""
    return url

def format_arxiv_paper(arxiv_id: str) -> str:
    """arXiv paper."""
    return f"https://arxiv.org/abs/{arxiv_id}"

def format_doi(doi: str) -> str:
    """Digital Object Identifier."""
    if doi.startswith('10.'):
        return f"https://doi.org/{doi}"
    return doi

def format_isbn(isbn: str) -> str:
    """ISBN book lookup."""
    isbn_clean = isbn.replace('-', '').replace(' ', '')
    return f"https://www.worldcat.org/isbn/{isbn_clean}"

def format_wikipedia(article: str, language: str = "en") -> str:
    """Wikipedia article."""
    return f"https://{language}.wikipedia.org/wiki/{_url_encode(article)}"

def format_google_search(query: str) -> str:
    """Google search."""
    return f"https://www.google.com/search?q={_url_encode(query)}"

def format_amazon_product(asin: str, country: str = "com") -> str:
    """Amazon product."""
    return f"https://www.amazon.{country}/dp/{asin}"


# =============================================================================
# PLAIN DATA
# =============================================================================

def format_plain_text(text: str) -> str:
    """Plain text - no formatting."""
    return text

def format_normal(text: str) -> str:
    """Normal text for simple 1-2 line sentences or messages."""
    return text.strip()

def format_json_data(data: dict) -> str:
    """JSON data."""
    import json
    return json.dumps(data, separators=(',', ':'))

def format_base64_data(data: str) -> str:
    """Base64 encoded data."""
    import base64
    return base64.b64encode(data.encode()).decode()


# =============================================================================
# REGIONAL PAYMENT SYSTEMS
# =============================================================================

def format_alipay(user_id: str, amount: str = "") -> str:
    """Alipay (China)."""
    if amount:
        return f"alipays://platformapi/startapp?appId=20000067&url=https://qr.alipay.com/{user_id}&amount={amount}"
    return f"alipays://platformapi/startapp?appId=20000067&url=https://qr.alipay.com/{user_id}"

def format_wechat_pay(wxpay_url: str) -> str:
    """WeChat Pay (China)."""
    return wxpay_url  # WeChat uses dynamic URLs

def format_wechat_profile(wechat_id: str) -> str:
    """WeChat profile/add friend."""
    return f"weixin://contacts/profile/{wechat_id}"

def format_pix_brazil(pix_key: str, amount: str = "", description: str = "") -> str:
    """PIX Payment (Brazil)."""
    # Simplified - full format is EMV QR Code
    params = {'chave': pix_key}
    if amount:
        params['valor'] = amount
    if description:
        params['descricao'] = description
    return f"pix://pay?{urllib.parse.urlencode(params)}"

def format_mpesa(phone: str, amount: str = "", account: str = "") -> str:
    """M-Pesa (Africa)."""
    base = f"mpesa://pay?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    if account:
        base += f"&account={account}"
    return base

def format_gcash(phone: str, amount: str = "") -> str:
    """GCash (Philippines)."""
    base = f"gcash://send?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    return base

def format_paymaya(phone: str, amount: str = "") -> str:
    """PayMaya/Maya (Philippines)."""
    base = f"maya://pay?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    return base

def format_grabpay(phone: str) -> str:
    """GrabPay (Southeast Asia)."""
    return f"grab://pay?phone={phone}"

def format_gopay(phone: str, amount: str = "") -> str:
    """GoPay (Indonesia)."""
    base = f"gojek://gopay/pay?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    return base

def format_ovo(phone: str) -> str:
    """OVO (Indonesia)."""
    return f"ovo://pay?phone={phone}"

def format_dana(phone: str) -> str:
    """DANA (Indonesia)."""
    return f"dana://pay?phone={phone}"

def format_kakao_pay(kakao_id: str) -> str:
    """Kakao Pay (Korea)."""
    return f"kakaopay://pay?id={kakao_id}"

def format_naver_pay(merchant_id: str) -> str:
    """Naver Pay (Korea)."""
    return f"naverpay://pay?merchantId={merchant_id}"

def format_toss(phone: str, amount: str = "") -> str:
    """Toss (Korea)."""
    base = f"supertoss://send?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    return base

def format_line_pay(line_id: str) -> str:
    """LINE Pay (Japan/Taiwan/Thailand)."""
    return f"line://pay/request?to={line_id}"

def format_rakuten_pay(merchant_id: str) -> str:
    """Rakuten Pay (Japan)."""
    return f"rakutenpay://pay?merchantId={merchant_id}"

def format_paypay_japan(paypay_id: str) -> str:
    """PayPay (Japan)."""
    return f"paypay://pay?id={paypay_id}"

def format_promptpay(phone_or_id: str, amount: str = "") -> str:
    """PromptPay (Thailand)."""
    base = f"promptpay://{phone_or_id}"
    if amount:
        base += f"?amount={amount}"
    return base

def format_truemoney(phone: str) -> str:
    """TrueMoney Wallet (Thailand)."""
    return f"truemoney://pay?phone={phone}"

def format_momo_vietnam(phone: str, amount: str = "") -> str:
    """MoMo (Vietnam)."""
    base = f"momo://pay?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    return base

def format_zalopay(phone: str) -> str:
    """ZaloPay (Vietnam)."""
    return f"zalopay://pay?phone={phone}"

def format_vietqr(bank_id: str, account: str, amount: str = "", description: str = "") -> str:
    """VietQR (Vietnam banking)."""
    base = f"vietqr://{bank_id}/{account}"
    params = {}
    if amount:
        params['amount'] = amount
    if description:
        params['desc'] = description
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base

def format_touch_n_go(phone: str) -> str:
    """Touch 'n Go (Malaysia)."""
    return f"tng://pay?phone={phone}"

def format_boost(phone: str) -> str:
    """Boost (Malaysia)."""
    return f"boost://pay?phone={phone}"

def format_paysera(phone: str, amount: str = "") -> str:
    """Paysera (Lithuania/EU)."""
    base = f"paysera://pay?phone={phone}"
    if amount:
        base += f"&amount={amount}"
    return base

def format_revolut(username: str, amount: str = "") -> str:
    """Revolut payment request."""
    base = f"https://revolut.me/{username}"
    if amount:
        return f"{base}/{amount}"
    return base

def format_wise(email: str, amount: str = "", currency: str = "USD") -> str:
    """Wise (TransferWise) payment."""
    params = {'email': email}
    if amount:
        params['amount'] = amount
        params['currency'] = currency
    return f"https://wise.com/pay/?{urllib.parse.urlencode(params)}"

def format_klarna(merchant_id: str, order_id: str) -> str:
    """Klarna payment."""
    return f"klarna://pay?merchantId={merchant_id}&orderId={order_id}"

def format_afterpay(merchant_id: str, order_id: str) -> str:
    """Afterpay payment."""
    return f"afterpay://pay?merchantId={merchant_id}&orderId={order_id}"

def format_affirm(checkout_id: str) -> str:
    """Affirm payment."""
    return f"affirm://checkout?id={checkout_id}"

def format_zelle(email_or_phone: str, amount: str = "", memo: str = "") -> str:
    """Zelle payment (US)."""
    params = {'recipient': email_or_phone}
    if amount:
        params['amount'] = amount
    if memo:
        params['memo'] = memo
    return f"zelle://pay?{urllib.parse.urlencode(params)}"


# =============================================================================
# ASIAN SOCIAL PLATFORMS
# =============================================================================

def format_weibo(user_id: str) -> str:
    """Weibo (China)."""
    return f"https://weibo.com/u/{user_id}"

def format_douyin(user_id: str) -> str:
    """Douyin (TikTok China)."""
    return f"https://www.douyin.com/user/{user_id}"

def format_xiaohongshu(user_id: str) -> str:
    """Xiaohongshu/RED (China)."""
    return f"https://www.xiaohongshu.com/user/profile/{user_id}"

def format_bilibili(user_id: str) -> str:
    """Bilibili (China)."""
    return f"https://space.bilibili.com/{user_id}"

def format_qq(qq_number: str) -> str:
    """QQ profile (China)."""
    return f"mqqwpa://im/chat?chat_type=wpa&uin={qq_number}"

def format_vk(username: str) -> str:
    """VK/VKontakte (Russia)."""
    return f"https://vk.com/{username}"

def format_ok_ru(user_id: str) -> str:
    """Odnoklassniki (Russia)."""
    return f"https://ok.ru/profile/{user_id}"

def format_line_profile(line_id: str) -> str:
    """LINE profile (Japan/Taiwan/Thailand)."""
    return f"https://line.me/ti/p/{line_id}"

def format_line_add_friend(line_id: str) -> str:
    """LINE add friend."""
    return f"https://line.me/R/ti/p/@{line_id}"

def format_kakaotalk(kakao_id: str) -> str:
    """KakaoTalk profile (Korea)."""
    return f"https://open.kakao.com/o/{kakao_id}"

def format_zalo(phone: str) -> str:
    """Zalo (Vietnam)."""
    return f"https://zalo.me/{phone}"

def format_naver_blog(blog_id: str) -> str:
    """Naver Blog (Korea)."""
    return f"https://blog.naver.com/{blog_id}"

def format_mixi(user_id: str) -> str:
    """Mixi (Japan)."""
    return f"https://mixi.jp/show_profile.pl?id={user_id}"

def format_baidu_tieba(tieba_name: str) -> str:
    """Baidu Tieba (China)."""
    return f"https://tieba.baidu.com/f?kw={_url_encode(tieba_name)}"


# =============================================================================
# TRAVEL & TRANSPORTATION
# =============================================================================

def format_airline_boarding_pass(
    pnr: str,
    passenger_name: str,
    flight_number: str,
    departure: str,
    arrival: str,
    date: str,
    seat: str = ""
) -> str:
    """Airline boarding pass (IATA BCBP simplified)."""
    # Simplified format - real BCBP is complex
    data = f"M1{passenger_name[:20]:<20}E{pnr:<7}{departure}{arrival}{flight_number:<5}{date}{seat:<4}"
    return data

def format_train_ticket(
    pnr: str,
    passenger: str,
    train_number: str,
    from_station: str,
    to_station: str,
    date: str,
    seat: str = ""
) -> str:
    """Train ticket QR data."""
    return f"TRAIN:{pnr}|{passenger}|{train_number}|{from_station}->{to_station}|{date}|{seat}"

def format_bus_ticket(
    ticket_id: str,
    route: str,
    date: str,
    seat: str = ""
) -> str:
    """Bus ticket."""
    return f"BUS:{ticket_id}|{route}|{date}|{seat}"

def format_booking_com(property_id: str) -> str:
    """Booking.com hotel."""
    return f"https://www.booking.com/hotel/{property_id}"

def format_airbnb_listing(listing_id: str) -> str:
    """Airbnb listing."""
    return f"https://www.airbnb.com/rooms/{listing_id}"

def format_tripadvisor(attraction_id: str) -> str:
    """TripAdvisor attraction."""
    return f"https://www.tripadvisor.com/Attraction_Review-{attraction_id}"

def format_ola_ride(lat: float, lon: float) -> str:
    """Ola ride (India)."""
    return f"olacabs://Book?lat={lat}&lng={lon}"

def format_grab_ride(lat: float, lon: float) -> str:
    """Grab ride (Southeast Asia)."""
    return f"grab://open?lat={lat}&lng={lon}"

def format_gojek_ride(lat: float, lon: float) -> str:
    """Gojek ride (Indonesia)."""
    return f"gojek://goride?lat={lat}&lng={lon}"

def format_didi_ride(lat: float, lon: float) -> str:
    """DiDi ride (China/Global)."""
    return f"didiglobal://ride?lat={lat}&lng={lon}"

def format_bolt_ride(lat: float, lon: float) -> str:
    """Bolt ride (Europe/Africa)."""
    return f"bolt://ride?lat={lat}&lng={lon}"

def format_cabify_ride(lat: float, lon: float) -> str:
    """Cabify ride (Spain/LatAm)."""
    return f"cabify://ride?lat={lat}&lng={lon}"

def format_lime_scooter(lat: float, lon: float) -> str:
    """Lime scooter/bike."""
    return f"lime://ride?lat={lat}&lng={lon}"

def format_bird_scooter(lat: float, lon: float) -> str:
    """Bird scooter."""
    return f"bird://ride?lat={lat}&lng={lon}"

def format_ev_charging_station(station_id: str, network: str = "chargepoint") -> str:
    """EV charging station."""
    networks = {
        "chargepoint": f"https://na.chargepoint.com/station/{station_id}",
        "tesla": f"https://www.tesla.com/supercharger/{station_id}",
        "electrify_america": f"https://www.electrifyamerica.com/locate/{station_id}",
    }
    return networks.get(network, f"evcharging://{network}/{station_id}")


# =============================================================================
# FOOD DELIVERY & RESTAURANTS
# =============================================================================

def format_ubereats_restaurant(restaurant_id: str) -> str:
    """Uber Eats restaurant."""
    return f"ubereats://restaurant/{restaurant_id}"

def format_doordash_restaurant(restaurant_slug: str) -> str:
    """DoorDash restaurant."""
    return f"https://www.doordash.com/store/{restaurant_slug}"

def format_grubhub_restaurant(restaurant_id: str) -> str:
    """Grubhub restaurant."""
    return f"grubhub://restaurant/{restaurant_id}"

def format_postmates_restaurant(restaurant_id: str) -> str:
    """Postmates restaurant."""
    return f"postmates://restaurant/{restaurant_id}"

def format_deliveroo_restaurant(restaurant_slug: str) -> str:
    """Deliveroo restaurant."""
    return f"https://deliveroo.com/menu/{restaurant_slug}"

def format_justeat_restaurant(restaurant_id: str) -> str:
    """Just Eat restaurant."""
    return f"https://www.just-eat.com/restaurants/{restaurant_id}"

def format_zomato_restaurant(restaurant_id: str) -> str:
    """Zomato restaurant."""
    return f"zomato://restaurant/{restaurant_id}"

def format_swiggy_restaurant(restaurant_id: str) -> str:
    """Swiggy restaurant (India)."""
    return f"swiggy://restaurant/{restaurant_id}"

def format_foodpanda_restaurant(restaurant_id: str) -> str:
    """Foodpanda restaurant."""
    return f"foodpanda://restaurant/{restaurant_id}"

def format_grabfood_restaurant(restaurant_id: str) -> str:
    """GrabFood restaurant."""
    return f"grab://food/restaurant/{restaurant_id}"

def format_gofood_restaurant(restaurant_id: str) -> str:
    """GoFood restaurant (Indonesia)."""
    return f"gojek://gofood/restaurant/{restaurant_id}"

def format_meituan_restaurant(restaurant_id: str) -> str:
    """Meituan (China)."""
    return f"meituan://restaurant/{restaurant_id}"

def format_eleme_restaurant(restaurant_id: str) -> str:
    """Ele.me (China)."""
    return f"eleme://restaurant/{restaurant_id}"

def format_yelp_business(business_id: str) -> str:
    """Yelp business page."""
    return f"yelp://biz/{business_id}"

def format_opentable_restaurant(restaurant_id: str) -> str:
    """OpenTable restaurant reservation."""
    return f"https://www.opentable.com/r/{restaurant_id}"

def format_resy_restaurant(restaurant_slug: str) -> str:
    """Resy restaurant reservation."""
    return f"https://resy.com/cities/ny/{restaurant_slug}"

def format_restaurant_menu(menu_url: str) -> str:
    """Restaurant menu link."""
    return menu_url


# =============================================================================
# DATING APPS
# =============================================================================

def format_tinder_profile(user_id: str) -> str:
    """Tinder profile."""
    return f"tinder://profile/{user_id}"

def format_bumble_profile(user_id: str) -> str:
    """Bumble profile."""
    return f"bumble://profile/{user_id}"

def format_hinge_profile(user_id: str) -> str:
    """Hinge profile."""
    return f"hinge://profile/{user_id}"

def format_okcupid_profile(username: str) -> str:
    """OkCupid profile."""
    return f"https://www.okcupid.com/profile/{username}"

def format_match_profile(user_id: str) -> str:
    """Match.com profile."""
    return f"https://www.match.com/profile/{user_id}"

def format_badoo_profile(user_id: str) -> str:
    """Badoo profile."""
    return f"badoo://profile/{user_id}"

def format_grindr_profile(user_id: str) -> str:
    """Grindr profile."""
    return f"grindr://profile/{user_id}"

def format_her_profile(user_id: str) -> str:
    """HER dating profile."""
    return f"her://profile/{user_id}"


# =============================================================================
# JOB & PROFESSIONAL PLATFORMS
# =============================================================================

def format_indeed_job(job_id: str) -> str:
    """Indeed job listing."""
    return f"https://www.indeed.com/viewjob?jk={job_id}"

def format_glassdoor_company(company_id: str) -> str:
    """Glassdoor company."""
    return f"https://www.glassdoor.com/Overview/{company_id}"

def format_monster_job(job_id: str) -> str:
    """Monster job listing."""
    return f"https://www.monster.com/job-openings/{job_id}"

def format_ziprecruiter_job(job_id: str) -> str:
    """ZipRecruiter job."""
    return f"https://www.ziprecruiter.com/jobs/{job_id}"

def format_upwork_profile(username: str) -> str:
    """Upwork freelancer profile."""
    return f"https://www.upwork.com/freelancers/{username}"

def format_fiverr_gig(gig_slug: str) -> str:
    """Fiverr gig."""
    return f"https://www.fiverr.com{gig_slug}"

def format_toptal_profile(username: str) -> str:
    """Toptal profile."""
    return f"https://www.toptal.com/resume/{username}"

def format_angellist_company(company_slug: str) -> str:
    """AngelList/Wellfound company."""
    return f"https://angel.co/company/{company_slug}"

def format_huntr_job(job_id: str) -> str:
    """Huntr job tracking."""
    return f"huntr://job/{job_id}"

def format_handshake_job(job_id: str) -> str:
    """Handshake (college recruiting)."""
    return f"https://app.joinhandshake.com/jobs/{job_id}"


# =============================================================================
# E-COMMERCE
# =============================================================================

def format_shopify_product(store: str, product_handle: str) -> str:
    """Shopify product."""
    return f"https://{store}.myshopify.com/products/{product_handle}"

def format_etsy_product(listing_id: str) -> str:
    """Etsy product listing."""
    return f"https://www.etsy.com/listing/{listing_id}"

def format_ebay_item(item_id: str) -> str:
    """eBay item."""
    return f"https://www.ebay.com/itm/{item_id}"

def format_aliexpress_product(product_id: str) -> str:
    """AliExpress product."""
    return f"https://www.aliexpress.com/item/{product_id}.html"

def format_wish_product(product_id: str) -> str:
    """Wish product."""
    return f"https://www.wish.com/product/{product_id}"

def format_walmart_product(product_id: str) -> str:
    """Walmart product."""
    return f"https://www.walmart.com/ip/{product_id}"

def format_target_product(product_id: str) -> str:
    """Target product."""
    return f"https://www.target.com/p/-/A-{product_id}"

def format_bestbuy_product(sku: str) -> str:
    """Best Buy product."""
    return f"https://www.bestbuy.com/site/{sku}.p"

def format_flipkart_product(product_id: str) -> str:
    """Flipkart product (India)."""
    return f"https://www.flipkart.com/product/{product_id}"

def format_lazada_product(product_id: str) -> str:
    """Lazada product (Southeast Asia)."""
    return f"https://www.lazada.com/products/{product_id}.html"

def format_shopee_product(product_id: str) -> str:
    """Shopee product (Southeast Asia)."""
    return f"https://shopee.com/product/{product_id}"

def format_tokopedia_product(product_id: str) -> str:
    """Tokopedia product (Indonesia)."""
    return f"https://www.tokopedia.com/p/{product_id}"

def format_taobao_product(item_id: str) -> str:
    """Taobao product (China)."""
    return f"https://item.taobao.com/item.htm?id={item_id}"

def format_jd_product(sku: str) -> str:
    """JD.com product (China)."""
    return f"https://item.jd.com/{sku}.html"

def format_mercari_product(product_id: str) -> str:
    """Mercari product."""
    return f"https://www.mercari.com/us/item/{product_id}"

def format_poshmark_listing(listing_id: str) -> str:
    """Poshmark listing."""
    return f"https://poshmark.com/listing/{listing_id}"

def format_depop_product(product_id: str) -> str:
    """Depop product."""
    return f"https://www.depop.com/products/{product_id}"

def format_product_barcode(barcode: str, barcode_type: str = "EAN13") -> str:
    """Product barcode lookup."""
    return f"https://www.barcodelookup.com/{barcode}"


# =============================================================================
# NFT & WEB3
# =============================================================================

def format_opensea_nft(contract: str, token_id: str) -> str:
    """OpenSea NFT."""
    return f"https://opensea.io/assets/ethereum/{contract}/{token_id}"

def format_rarible_nft(contract: str, token_id: str) -> str:
    """Rarible NFT."""
    return f"https://rarible.com/token/{contract}:{token_id}"

def format_foundation_nft(token_id: str) -> str:
    """Foundation NFT."""
    return f"https://foundation.app/token/{token_id}"

def format_looksrare_nft(contract: str, token_id: str) -> str:
    """LooksRare NFT."""
    return f"https://looksrare.org/collections/{contract}/{token_id}"

def format_metamask_connect(dapp_url: str) -> str:
    """MetaMask dApp connection."""
    return f"https://metamask.app.link/dapp/{dapp_url}"

def format_walletconnect(uri: str) -> str:
    """WalletConnect URI."""
    return uri  # WalletConnect URIs are already formatted

def format_ens_domain(domain: str) -> str:
    """ENS domain lookup."""
    return f"https://app.ens.domains/name/{domain}"

def format_ipfs_gateway(cid: str) -> str:
    """IPFS content via gateway."""
    return f"https://ipfs.io/ipfs/{cid}"

def format_arweave(tx_id: str) -> str:
    """Arweave permanent storage."""
    return f"https://arweave.net/{tx_id}"

def format_etherscan_tx(tx_hash: str) -> str:
    """Etherscan transaction."""
    return f"https://etherscan.io/tx/{tx_hash}"

def format_etherscan_address(address: str) -> str:
    """Etherscan address."""
    return f"https://etherscan.io/address/{address}"

def format_polygonscan_tx(tx_hash: str) -> str:
    """Polygonscan transaction."""
    return f"https://polygonscan.com/tx/{tx_hash}"

def format_bscscan_tx(tx_hash: str) -> str:
    """BSCScan transaction."""
    return f"https://bscscan.com/tx/{tx_hash}"

def format_solscan_tx(tx_hash: str) -> str:
    """Solscan transaction."""
    return f"https://solscan.io/tx/{tx_hash}"

def format_magic_eden_nft(mint_address: str) -> str:
    """Magic Eden NFT (Solana)."""
    return f"https://magiceden.io/item-details/{mint_address}"


# =============================================================================
# PODCASTS & AUDIO
# =============================================================================

def format_apple_podcasts(podcast_id: str) -> str:
    """Apple Podcasts."""
    return f"https://podcasts.apple.com/podcast/id{podcast_id}"

def format_google_podcasts(feed_url: str) -> str:
    """Google Podcasts."""
    return f"https://podcasts.google.com/?feed={_url_encode(feed_url)}"

def format_spotify_podcast(show_id: str) -> str:
    """Spotify podcast."""
    return f"https://open.spotify.com/show/{show_id}"

def format_spotify_episode(episode_id: str) -> str:
    """Spotify podcast episode."""
    return f"https://open.spotify.com/episode/{episode_id}"

def format_overcast_podcast(podcast_id: str) -> str:
    """Overcast podcast."""
    return f"overcast://podcast/{podcast_id}"

def format_pocketcasts_podcast(podcast_uuid: str) -> str:
    """Pocket Casts podcast."""
    return f"pktc://subscribe/{podcast_uuid}"

def format_castbox_podcast(podcast_id: str) -> str:
    """Castbox podcast."""
    return f"https://castbox.fm/channel/id{podcast_id}"

def format_stitcher_show(show_id: str) -> str:
    """Stitcher show."""
    return f"https://www.stitcher.com/show/{show_id}"

def format_audible_book(asin: str) -> str:
    """Audible audiobook."""
    return f"https://www.audible.com/pd/{asin}"

def format_podcast_rss(feed_url: str) -> str:
    """Podcast RSS feed."""
    return f"podcast://{feed_url.replace('https://', '').replace('http://', '')}"

def format_anchor_profile(username: str) -> str:
    """Anchor.fm profile."""
    return f"https://anchor.fm/{username}"


# =============================================================================
# NEWS & PUBLICATIONS
# =============================================================================

def format_medium_article(article_slug: str) -> str:
    """Medium article."""
    return f"https://medium.com/{article_slug}"

def format_substack_newsletter(publication: str) -> str:
    """Substack newsletter."""
    return f"https://{publication}.substack.com"

def format_substack_post(publication: str, post_slug: str) -> str:
    """Substack post."""
    return f"https://{publication}.substack.com/p/{post_slug}"

def format_mirror_xyz(address: str) -> str:
    """Mirror.xyz blog."""
    return f"https://mirror.xyz/{address}"

def format_hackernews_item(item_id: str) -> str:
    """Hacker News item."""
    return f"https://news.ycombinator.com/item?id={item_id}"

def format_producthunt_product(slug: str) -> str:
    """Product Hunt."""
    return f"https://www.producthunt.com/posts/{slug}"

def format_nytimes_article(url: str) -> str:
    """New York Times article."""
    return url

def format_wsj_article(url: str) -> str:
    """Wall Street Journal article."""
    return url

def format_guardian_article(url: str) -> str:
    """The Guardian article."""
    return url

def format_bbc_article(url: str) -> str:
    """BBC article."""
    return url

def format_reuters_article(url: str) -> str:
    """Reuters article."""
    return url


# =============================================================================
# GOVERNMENT & OFFICIAL
# =============================================================================

def format_covid_vaccine_cert(cert_data: str) -> str:
    """COVID vaccine certificate (SMART Health Card)."""
    return f"shc:/{cert_data}"

def format_eu_digital_covid_cert(cert_data: str) -> str:
    """EU Digital COVID Certificate."""
    return f"HC1:{cert_data}"

def format_aadhaar_verify(aadhaar_number: str) -> str:
    """Aadhaar verification (India)."""
    return f"aadhaar://verify?uid={aadhaar_number}"

def format_digilocker(doc_uri: str) -> str:
    """DigiLocker document (India)."""
    return f"digilocker://doc/{doc_uri}"

def format_mygov_service(service_id: str, country: str = "in") -> str:
    """Government service portal."""
    return f"https://mygov.{country}/service/{service_id}"

def format_uscis_case(receipt_number: str) -> str:
    """USCIS case status."""
    return f"https://egov.uscis.gov/casestatus/landing.do?receipt={receipt_number}"

def format_passport_mrz(mrz_line1: str, mrz_line2: str) -> str:
    """Passport MRZ data."""
    return f"{mrz_line1}\n{mrz_line2}"

def format_drivers_license_pdf417(data: str) -> str:
    """Driver's license data (AAMVA format)."""
    return data


# =============================================================================
# EDUCATION
# =============================================================================

def format_coursera_course(course_slug: str) -> str:
    """Coursera course."""
    return f"https://www.coursera.org/learn/{course_slug}"

def format_udemy_course(course_id: str) -> str:
    """Udemy course."""
    return f"https://www.udemy.com/course/{course_id}"

def format_edx_course(course_id: str) -> str:
    """edX course."""
    return f"https://www.edx.org/course/{course_id}"

def format_khan_academy(content_id: str) -> str:
    """Khan Academy content."""
    return f"https://www.khanacademy.org/{content_id}"

def format_skillshare_class(class_slug: str) -> str:
    """Skillshare class."""
    return f"https://www.skillshare.com/classes/{class_slug}"

def format_linkedin_learning(course_slug: str) -> str:
    """LinkedIn Learning course."""
    return f"https://www.linkedin.com/learning/{course_slug}"

def format_pluralsight_course(course_slug: str) -> str:
    """Pluralsight course."""
    return f"https://www.pluralsight.com/courses/{course_slug}"

def format_codecademy_course(course_slug: str) -> str:
    """Codecademy course."""
    return f"https://www.codecademy.com/learn/{course_slug}"

def format_duolingo_profile(username: str) -> str:
    """Duolingo profile."""
    return f"https://www.duolingo.com/profile/{username}"

def format_quizlet_set(set_id: str) -> str:
    """Quizlet flashcard set."""
    return f"https://quizlet.com/{set_id}"

def format_google_classroom(class_code: str) -> str:
    """Google Classroom join code."""
    return f"https://classroom.google.com/c/{class_code}"

def format_canvas_course(domain: str, course_id: str) -> str:
    """Canvas LMS course."""
    return f"https://{domain}/courses/{course_id}"

def format_student_id(
    student_id: str,
    name: str,
    institution: str,
    valid_until: str = ""
) -> str:
    """Student ID card data."""
    data = f"STUDENT:{student_id}|{name}|{institution}"
    if valid_until:
        data += f"|{valid_until}"
    return data


# =============================================================================
# HEALTHCARE
# =============================================================================

def format_medical_record_id(mrn: str, facility: str) -> str:
    """Medical record number."""
    return f"MRN:{facility}:{mrn}"

def format_prescription(
    rx_number: str,
    medication: str,
    dosage: str,
    pharmacy: str = ""
) -> str:
    """Prescription data."""
    data = f"RX:{rx_number}|{medication}|{dosage}"
    if pharmacy:
        data += f"|{pharmacy}"
    return data

def format_health_insurance_card(
    member_id: str,
    group_number: str,
    plan_name: str,
    payer_id: str = ""
) -> str:
    """Health insurance card data."""
    data = f"INS:{member_id}|{group_number}|{plan_name}"
    if payer_id:
        data += f"|{payer_id}"
    return data

def format_fhir_patient(fhir_url: str, patient_id: str) -> str:
    """FHIR patient resource."""
    return f"{fhir_url}/Patient/{patient_id}"

def format_apple_health_record(record_type: str) -> str:
    """Apple Health record."""
    return f"x-apple-health://record/{record_type}"

def format_mychart_appointment(org_id: str, appointment_id: str) -> str:
    """MyChart appointment."""
    return f"mychart://appointment?org={org_id}&id={appointment_id}"


# =============================================================================
# TICKETING & EVENTS
# =============================================================================

def format_eventbrite_event(event_id: str) -> str:
    """Eventbrite event."""
    return f"https://www.eventbrite.com/e/{event_id}"

def format_ticketmaster_event(event_id: str) -> str:
    """Ticketmaster event."""
    return f"https://www.ticketmaster.com/event/{event_id}"

def format_stubhub_event(event_id: str) -> str:
    """StubHub event."""
    return f"https://www.stubhub.com/event/{event_id}"

def format_seatgeek_event(event_id: str) -> str:
    """SeatGeek event."""
    return f"https://seatgeek.com/e/{event_id}"

def format_meetup_event(group: str, event_id: str) -> str:
    """Meetup event."""
    return f"https://www.meetup.com/{group}/events/{event_id}"

def format_luma_event(event_id: str) -> str:
    """Luma event."""
    return f"https://lu.ma/{event_id}"

def format_movie_ticket(
    theater: str,
    movie: str,
    showtime: str,
    seat: str = "",
    confirmation: str = ""
) -> str:
    """Movie ticket."""
    data = f"MOVIE:{theater}|{movie}|{showtime}"
    if seat:
        data += f"|{seat}"
    if confirmation:
        data += f"|{confirmation}"
    return data

def format_concert_ticket(
    venue: str,
    artist: str,
    date: str,
    seat: str = "",
    barcode: str = ""
) -> str:
    """Concert ticket."""
    data = f"CONCERT:{venue}|{artist}|{date}"
    if seat:
        data += f"|{seat}"
    if barcode:
        data += f"|{barcode}"
    return data

def format_sports_ticket(
    venue: str,
    event: str,
    date: str,
    section: str = "",
    row: str = "",
    seat: str = ""
) -> str:
    """Sports event ticket."""
    data = f"SPORTS:{venue}|{event}|{date}"
    if section:
        data += f"|{section}"
    if row:
        data += f"|{row}"
    if seat:
        data += f"|{seat}"
    return data

def format_museum_ticket(
    museum: str,
    date: str,
    ticket_type: str = "adult",
    ticket_id: str = ""
) -> str:
    """Museum ticket."""
    data = f"MUSEUM:{museum}|{date}|{ticket_type}"
    if ticket_id:
        data += f"|{ticket_id}"
    return data


# =============================================================================
# LOYALTY & MEMBERSHIP
# =============================================================================

def format_loyalty_card(
    program_name: str,
    member_id: str,
    points: str = ""
) -> str:
    """Loyalty program card."""
    data = f"LOYALTY:{program_name}:{member_id}"
    if points:
        data += f":{points}"
    return data

def format_gym_membership(
    gym_name: str,
    member_id: str,
    valid_until: str = ""
) -> str:
    """Gym membership card."""
    data = f"GYM:{gym_name}:{member_id}"
    if valid_until:
        data += f":{valid_until}"
    return data

def format_library_card(
    library: str,
    card_number: str,
    patron_name: str = ""
) -> str:
    """Library card."""
    data = f"LIBRARY:{library}:{card_number}"
    if patron_name:
        data += f":{patron_name}"
    return data

def format_costco_membership(member_id: str) -> str:
    """Costco membership."""
    return f"costco://member/{member_id}"

def format_amazon_prime(member_id: str) -> str:
    """Amazon Prime membership."""
    return f"amazon://prime/member/{member_id}"

def format_airline_frequent_flyer(
    airline: str,
    member_id: str,
    tier: str = ""
) -> str:
    """Airline frequent flyer."""
    data = f"FFP:{airline}:{member_id}"
    if tier:
        data += f":{tier}"
    return data

def format_hotel_rewards(
    program: str,
    member_id: str,
    tier: str = ""
) -> str:
    """Hotel rewards program."""
    data = f"HOTEL:{program}:{member_id}"
    if tier:
        data += f":{tier}"
    return data


# =============================================================================
# REAL ESTATE
# =============================================================================

def format_zillow_listing(zpid: str) -> str:
    """Zillow listing."""
    return f"https://www.zillow.com/homedetails/{zpid}_zpid"

def format_realtor_listing(listing_id: str) -> str:
    """Realtor.com listing."""
    return f"https://www.realtor.com/realestateandhomes-detail/{listing_id}"

def format_redfin_listing(listing_id: str) -> str:
    """Redfin listing."""
    return f"https://www.redfin.com{listing_id}"

def format_trulia_listing(listing_id: str) -> str:
    """Trulia listing."""
    return f"https://www.trulia.com/p/{listing_id}"

def format_apartments_listing(listing_id: str) -> str:
    """Apartments.com listing."""
    return f"https://www.apartments.com/{listing_id}"

def format_property_qr(
    address: str,
    price: str = "",
    bedrooms: str = "",
    bathrooms: str = "",
    sqft: str = "",
    agent_phone: str = ""
) -> str:
    """Real estate property QR."""
    lines = [f"PROPERTY:{address}"]
    if price:
        lines.append(f"PRICE:{price}")
    if bedrooms:
        lines.append(f"BED:{bedrooms}")
    if bathrooms:
        lines.append(f"BATH:{bathrooms}")
    if sqft:
        lines.append(f"SQFT:{sqft}")
    if agent_phone:
        lines.append(f"TEL:{agent_phone}")
    return "\n".join(lines)



# =============================================================================
# HANDLER REGISTRY
# =============================================================================

# Map category -> { handler_name: handler_function }
HANDLERS = {
    "web": {
        "url": format_url,
        "deep_link": format_deep_link,
        "universal_link": format_universal_link,
    },
    "communication": {
        "phone_call": format_phone_call,
        "sms": format_sms,
        "mms": format_mms,
        "email": format_email,
        "facetime": format_facetime,
        "whatsapp": format_whatsapp,
        "telegram_user": format_telegram_user,
        "telegram_message": format_telegram_message,
        "signal": format_signal,
        "viber": format_viber,
        "skype_call": format_skype_call,
        "zoom": format_zoom_meeting,
        "google_meet": format_google_meet,
        "teams": format_microsoft_teams,
        "discord": format_discord_invite,
        "slack": format_slack_channel,
        "threema": format_threema_id,
        "session": format_session_id,
        "matrix": format_matrix_user,
        "xmpp": format_xmpp,
    },
    "social": {
        "instagram": format_instagram_profile,
        "facebook": format_facebook_profile,
        "twitter": format_twitter_profile,
        "linkedin": format_linkedin_profile,
        "youtube": format_youtube_channel,
        "youtube_video": format_youtube_video,
        "tiktok": format_tiktok_profile,
        "snapchat": format_snapchat_add,
        "pinterest": format_pinterest_profile,
        "reddit": format_reddit_profile,
        "reddit_sub": format_reddit_subreddit,
        "mastodon": format_mastodon_profile,
        "threads": format_threads_profile,
        "bluesky": format_bluesky_profile,
    },
    "finance": {
        "upi": format_upi,
        "paypal": format_paypal,
        "venmo": format_venmo,
        "cash_app": format_cash_app,
        "sepa": format_sepa_transfer,
        "bitcoin": format_bitcoin,
        "ethereum": format_ethereum,
        "usdt": format_usdt_erc20,
        "litecoin": format_litecoin,
        "dogecoin": format_dogecoin,
        "monero": format_monero,
        "solana": format_solana,
        "cardano": format_cardano,
        "ripple": format_ripple,
    },
    "contact": {
        "vcard": format_vcard,
        "mecard": format_mecard,
        "bizcard": format_bizcard,
    },
    "location": {
        "geo": format_geo_coordinates,
        "google_maps": format_google_maps_search,
        "google_directions": format_google_maps_directions,
        "apple_maps": format_apple_maps_search,
        "waze": format_waze_navigate,
        "uber": format_uber_ride,
        "what3words": format_what3words,
    },
    "calendar": {
        "ical_event": format_ical_event,
        "google_calendar": format_google_calendar_event,
        "outlook_calendar": format_outlook_calendar_event,
    },
    "wifi": {
        "wifi": format_wifi,
        "wifi_eap": format_wifi_eap,
    },
    "media": {
        "spotify": format_spotify_uri,
        "spotify_track": format_spotify_track,
        "apple_music": format_apple_music_url,
        "soundcloud": format_soundcloud_user,
        "twitch": format_twitch_channel,
        "steam": format_steam_profile,
        "steam_game": format_steam_game,
    },
    "stores": {
        "google_play": format_google_play_app,
        "app_store": format_apple_app_store,
        "microsoft_store": format_microsoft_store,
        "fdroid": format_fdroid_app,
    },
    "developer": {
        "github": format_github_profile,
        "github_repo": format_github_repo,
        "gitlab": format_gitlab_project,
        "npm": format_npm_package,
        "pypi": format_pypi_package,
        "docker": format_docker_hub,
        "google_drive": format_google_drive_file,
        "notion": format_notion_page,
        "figma": format_figma_file,
    },
    "security": {
        "totp": format_totp,
        "hotp": format_hotp,
        "ssh": format_ssh_connection,
        "wireguard": format_wireguard_config,
        "shadowsocks": format_shadowsocks,
    },
    "iot": {
        "home_assistant": format_home_assistant_webhook,
        "homekit": format_homekit_setup_code,
        "ifttt": format_ifttt_webhook,
        "ios_shortcut": format_ios_shortcut,
        "tasker": format_tasker_task,
    },
    "content": {
        "plain_text": format_plain_text,
        "normal": format_normal,
        "arxiv": format_arxiv_paper,
        "doi": format_doi,
        "isbn": format_isbn,
        "wikipedia": format_wikipedia,
        "google_search": format_google_search,
        "amazon": format_amazon_product,
    },
}


def get_all_handlers() -> dict:
    """Return the complete handler registry."""
    return HANDLERS

def get_handler(category: str, handler_name: str):
    """Get a specific handler function."""
    return HANDLERS.get(category, {}).get(handler_name)

def list_categories() -> list:
    """List all available categories."""
    return list(HANDLERS.keys())

def list_handlers_in_category(category: str) -> list:
    """List all handlers in a category."""
    return list(HANDLERS.get(category, {}).keys())
