from dataclasses import dataclass, field
from typing import (
    List, Optional, Dict, TypedDict, Literal, Union
)
from pathlib import Path

# =============================================================================
# TYPE ALIASES
# =============================================================================

GradientDirection = Literal["horizontal", "vertical", "diagonal", "radial"]


# All QR template types from handlers.py
TemplateType = Literal[
    # Web & URLs
    "url", "deep_link", "universal_link",
    
    # Communication
    "phone_call", "sms", "mms", "email", "facetime",
    "whatsapp", "whatsapp_business",
    "telegram_user", "telegram_message", "telegram_bot",
    "signal", "viber",
    "skype_call", "skype_chat", "skype_video",
    "zoom", "google_meet", "teams",
    "discord", "slack_channel", "slack_invite",
    "threema", "session", "matrix", "xmpp",
    
    # Social Media
    "instagram_profile", "instagram_post",
    "facebook_profile", "facebook_event", "facebook_group",
    "twitter_profile", "twitter_tweet", "twitter_compose",
    "linkedin_profile", "linkedin_company", "linkedin_share",
    "youtube_channel", "youtube_video", "youtube_playlist",
    "tiktok_profile", "tiktok_video",
    "snapchat_add", "snapchat_lens",
    "pinterest_profile", "pinterest_board",
    "reddit_profile", "reddit_subreddit", "reddit_post",
    "tumblr", "mastodon", "threads", "bluesky", "clubhouse", "bereal",
    
    # Finance & Payments
    "upi", "paytm", "paypal", "venmo", "cash_app",
    "sepa", "swiss_qr",
    "bitcoin", "ethereum", "ethereum_token",
    "usdt_erc20", "usdt_trc20",
    "litecoin", "dogecoin", "monero",
    "solana", "cardano", "ripple", "bnb", "polygon",
    
    # Contact Information
    "vcard", "mecard", "bizcard",
    
    # Location & Navigation
    "geo", "google_maps_search", "google_directions", "google_maps_place",
    "apple_maps_search", "apple_maps_directions",
    "waze_navigate", "waze_search",
    "uber", "lyft", "what3words", "plus_code",
    
    # Calendar & Events
    "ical", "google_calendar", "outlook_calendar",
    
    # WiFi & Network
    "wifi", "wifi_eap",
    
    # Media & Entertainment
    "spotify_uri", "spotify_track", "spotify_playlist", "spotify_artist",
    "apple_music", "apple_music_album",
    "soundcloud_user", "soundcloud_track",
    "bandcamp", "deezer", "tidal",
    "twitch_channel", "twitch_vod",
    "netflix", "prime_video", "imdb",
    "steam_profile", "steam_game", "epic_games", "playstation", "xbox",
    
    # App Stores
    "google_play", "google_play_deep",
    "app_store", "app_store_deep",
    "amazon_appstore", "huawei_appgallery", "samsung_galaxy",
    "microsoft_store", "fdroid",
    
    # Developer & Cloud
    "github_profile", "github_repo", "github_gist",
    "gitlab", "bitbucket",
    "npm", "pypi", "docker_hub",
    "dropbox", "google_drive_file", "google_drive_folder", "onedrive",
    "notion", "trello", "jira", "confluence", "figma", "miro",
    
    # Authentication & Security
    "totp", "hotp", "ssh", "sftp",
    "wireguard", "shadowsocks", "v2ray", "openvpn",
    
    # IoT & Smart Home
    "home_assistant_webhook", "home_assistant_entity",
    "homekit", "matter", "mqtt", "zigbee2mqtt",
    "ifttt", "ios_shortcut", "android_intent", "tasker",
    
    # Documents & Content
    "pdf", "arxiv", "doi", "isbn", "wikipedia",
    "google_search", "amazon_product",
    "plain_text", "normal", "json", "base64",
    
    # Regional Payments
    "alipay", "wechat_pay", "pix", "mpesa",
    "gcash", "paymaya", "grabpay", "gopay", "ovo", "dana",
    "kakao_pay", "naver_pay", "toss",
    "line_pay", "rakuten_pay", "paypay",
    "promptpay", "truemoney", "momo", "zalopay", "vietqr",
    "touch_n_go", "boost", "paysera", "revolut", "wise",
    "klarna", "afterpay", "affirm", "zelle",
    
    # Asian Social
    "weibo", "douyin", "xiaohongshu", "bilibili",
    "qq", "wechat_profile", "vk", "ok_ru",
    "line_profile", "line_add_friend", "kakaotalk", "zalo",
    "naver_blog", "mixi", "baidu_tieba",
    
    # Travel & Transportation
    "boarding_pass", "train_ticket", "bus_ticket",
    "booking_com", "airbnb", "tripadvisor",
    "ola", "grab", "gojek", "didi", "bolt", "cabify",
    "lime", "bird", "ev_charging",
    
    # Food Delivery
    "uber_eats", "doordash", "grubhub", "postmates",
    "deliveroo", "just_eat", "zomato", "swiggy",
    "foodpanda", "grabfood", "gofood", "meituan", "eleme",
    "yelp", "opentable", "resy",
    
    # Dating
    "tinder", "bumble", "hinge", "okcupid", "match", "badoo", "grindr", "her",
    
    # Jobs
    "indeed", "glassdoor", "monster", "ziprecruiter",
    "upwork", "fiverr", "toptal", "angellist", "huntr", "handshake",
    
    # E-commerce
    "shopify", "etsy", "ebay", "aliexpress", "wish",
    "walmart", "target", "bestbuy",
    "flipkart", "lazada", "shopee", "tokopedia", "taobao", "jd",
    "mercari", "poshmark", "depop", "barcode",
    
    # NFT & Web3
    "opensea", "rarible", "foundation", "looksrare",
    "metamask", "walletconnect", "ens", "ipfs", "arweave",
    "etherscan_tx", "etherscan_address", "polygonscan", "bscscan", "solscan",
    "magic_eden",
    
    # Podcasts
    "apple_podcasts", "google_podcasts", "spotify_podcast", "spotify_episode",
    "overcast", "pocket_casts", "castbox", "stitcher",
    "audible", "podcast_rss", "anchor",
    
    # News & Publications
    "medium", "substack", "substack_post", "mirror_xyz",
    "hackernews", "producthunt",
    "nytimes", "wsj", "guardian", "bbc", "reuters",
    
    # Government
    "covid_vaccine", "eu_covid_cert",
    "aadhaar", "digilocker", "mygov", "uscis",
    "passport_mrz", "drivers_license",
    
    # Education
    "coursera", "udemy", "edx", "khan_academy", "skillshare",
    "linkedin_learning", "pluralsight", "codecademy",
    "duolingo", "quizlet", "google_classroom", "canvas", "student_id",
    
    # Healthcare
    "medical_record", "prescription", "insurance_card",
    "fhir_patient", "apple_health", "mychart",
    
    # Ticketing
    "eventbrite", "ticketmaster", "stubhub", "seatgeek",
    "meetup", "luma",
    "movie_ticket", "concert_ticket", "sports_ticket", "museum_ticket",
    
    # Loyalty
    "loyalty_card", "gym_membership", "library_card",
    "costco", "amazon_prime", "frequent_flyer", "hotel_rewards",
    
    # Real Estate
    "zillow", "realtor", "redfin", "trulia", "apartments", "property_qr"
]

AVAILABLE_COLORS = [
    "red", "blue", "green", "yellow", "purple", "orange", "black", "white", "gray", 
    "brown", "pink", "cyan", "magenta", "lime", "violet", "indigo", "blueviolet", 
    "darkblue", "darkgreen", "darkorange", "darkred", "darkviolet", "darkyellow", 
    "greenyellow", "hotpink", "lawngreen", "lightblue", "lightgreen", "lightpink", 
    "lightsalmon", "lightseagreen", "lightskyblue", "lightslategray", "lightsteelblue", 
    "lightyellow", "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", 
    "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", 
    "mediumvioletred", "midnightblue", "mintcream", "mistyrose", "moccasin", 
    "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orangered", "orchid", 
    "palegoldenrod", "palegreen", "paleturquoise", "palevioletred", "papayawhip", 
    "peachpuff", "peru", "plum", "powderblue", "rosybrown", "royalblue", 
    "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell", "sienna", 
    "silver", "skyblue", "slateblue", "slategray", "slategrey", "snow", 
    "springgreen", "steelblue", "tan", "teal", "thistle", "tomato", "turquoise", 
    "wheat", "whitesmoke", "yellowgreen"
]

@dataclass
class QRConfig:
    """
    Configuration dataclass for QR code generation.
    
    This class encapsulates all settings required to generate a QR code,
    including QR specifications, output preferences, content data, and styling options.
    """
    
    
    # --- 1. MANDATORY FIELDS (Must come first) ---
    template_type: TemplateType = 'normal'  # Data handler template type from handlers.py
    output_dir: Union[str, Path] = None     # Directory to save generated QR code
    
    # --- 2. QR SPECIFICATIONS ---
    version: Optional[int] = 5              # QR version (1-40), controls data capacity. None = auto-fit
    error_correction: Literal["L", "M", "Q", "H"] = "H"  # Error correction: L(7%), M(15%), Q(25%), H(30%)
    module_drawer: Literal["rounded", "square", "circle", "gapped"] = 'rounded'  # Shape of QR modules
    box_size: int = 10                      # Pixel size of each module box
    border: int = 4                         # Quiet zone border width (in modules)
    
    # --- 3. OUTPUT SETTINGS ---
    output_type: Literal["svg", "png"] = "png"  # Output file format
    print_qr: bool = True                   # Print ASCII QR to terminal after generation
    
    # --- 4. CONTENT DATA ---
    data: Optional[Dict] = None             # Parameters passed to the template handler
    
    # --- 5. STYLING OPTIONS ---
    logo_path: Optional[Union[str, Path]] = None  # Path to logo image for center overlay
    gradient_direction: GradientDirection = None  # Gradient direction (None = solid color)
    # - horizontal: Left to right gradient
    # - vertical: Top to bottom gradient  
    # - diagonal: Corner to corner gradient
    # - radial: Center outward gradient
    gradient_colors: Optional[List] = None  # List of 3 colors: [back, center/left/top, edge/right/bottom]
    # Colors can be: RGB tuple (255,0,0), hex "#ff0000", or named "red"
    
    
    # --- 6. POST-INIT VALIDATION ---
    def __post_init__(self):
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if self.logo_path and isinstance(self.logo_path, str):
            self.logo_path = Path(self.logo_path)
