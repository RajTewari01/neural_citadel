"""
QR Studio Panel
================

Clean, aligned panel for QR code generation with:
- Searchable handler dropdown (300+ handlers)
- Dynamic input table (up to 20 fields per handler)
- SVG/Gradient mode toggle
- Gradient: Auto Random or Manual colors
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFrame, QScrollArea,
    QGridLayout, QCheckBox, QColorDialog, QFileDialog, QRadioButton,
    QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QColor
from infra.gui.theme import ThemeManager

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"

# =============================================================================
# HANDLER REGISTRY - All 374 handlers from handlers.py
# =============================================================================

# Dynamic handler loading from handlers.py
import sys
from pathlib import Path
import inspect

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from apps.qr_studio.data import handlers as handler_module
    
    def _get_handler_fields(handler_name: str) -> list:
        """Get field names for a handler function (string-compatible only)."""
        func = getattr(handler_module, f"format_{handler_name}", None)
        if func:
            sig = inspect.signature(func)
            fields = []
            for name, param in sig.parameters.items():
                # Skip parameters that expect complex types (dict, list, etc.)
                annotation = param.annotation
                if annotation != inspect.Parameter.empty:
                    # Skip dict, list, or Optional[dict] parameters
                    ann_str = str(annotation)
                    if 'dict' in ann_str.lower() or 'list' in ann_str.lower():
                        continue
                
                # Include required params and simple optional string params
                if param.default == inspect.Parameter.empty:
                    fields.append(name)
                elif len(fields) < 4 and param.default in ("", None):
                    # Only include optional params with empty string or None defaults
                    fields.append(name)
            return fields[:6]  # Max 6 fields per handler
        return ["data"]
    
    # Build handler categories dynamically
    HANDLER_CATEGORIES = {
        "🌐 Web & URLs": [
            ("url", _get_handler_fields("url"), "Website URL"),
            ("deep_link", _get_handler_fields("deep_link"), "App Deep Link"),
            ("universal_link", _get_handler_fields("universal_link"), "Universal Link"),
        ],
        "📞 Communication": [
            ("phone_call", _get_handler_fields("phone_call"), "Phone Call"),
            ("sms", _get_handler_fields("sms"), "SMS Message"),
            ("mms", _get_handler_fields("mms"), "MMS Message"),
            ("email", _get_handler_fields("email"), "Email"),
            ("facetime", _get_handler_fields("facetime"), "FaceTime"),
            ("whatsapp", _get_handler_fields("whatsapp"), "WhatsApp"),
            ("whatsapp_business", _get_handler_fields("whatsapp_business"), "WhatsApp Business"),
            ("telegram_user", _get_handler_fields("telegram_user"), "Telegram User"),
            ("telegram_message", _get_handler_fields("telegram_message"), "Telegram Message"),
            ("telegram_bot", _get_handler_fields("telegram_bot"), "Telegram Bot"),
            ("signal", _get_handler_fields("signal"), "Signal"),
            ("viber", _get_handler_fields("viber"), "Viber"),
            ("skype_call", _get_handler_fields("skype_call"), "Skype Call"),
            ("skype_chat", _get_handler_fields("skype_chat"), "Skype Chat"),
            ("skype_video", _get_handler_fields("skype_video"), "Skype Video"),
            ("zoom_meeting", _get_handler_fields("zoom_meeting"), "Zoom Meeting"),
            ("google_meet", _get_handler_fields("google_meet"), "Google Meet"),
            ("microsoft_teams", _get_handler_fields("microsoft_teams"), "MS Teams"),
            ("discord_invite", _get_handler_fields("discord_invite"), "Discord"),
            ("slack_channel", _get_handler_fields("slack_channel"), "Slack"),
            ("threema_id", _get_handler_fields("threema_id"), "Threema"),
            ("matrix_user", _get_handler_fields("matrix_user"), "Matrix"),
            ("xmpp", _get_handler_fields("xmpp"), "XMPP/Jabber"),
        ],
        "📱 Social Media": [
            ("instagram_profile", _get_handler_fields("instagram_profile"), "Instagram"),
            ("instagram_post", _get_handler_fields("instagram_post"), "Instagram Post"),
            ("facebook_profile", _get_handler_fields("facebook_profile"), "Facebook"),
            ("facebook_event", _get_handler_fields("facebook_event"), "FB Event"),
            ("facebook_group", _get_handler_fields("facebook_group"), "FB Group"),
            ("twitter_profile", _get_handler_fields("twitter_profile"), "Twitter/X"),
            ("twitter_tweet", _get_handler_fields("twitter_tweet"), "Tweet"),
            ("linkedin_profile", _get_handler_fields("linkedin_profile"), "LinkedIn"),
            ("linkedin_company", _get_handler_fields("linkedin_company"), "LinkedIn Co."),
            ("youtube_channel", _get_handler_fields("youtube_channel"), "YouTube"),
            ("youtube_video", _get_handler_fields("youtube_video"), "YT Video"),
            ("youtube_playlist", _get_handler_fields("youtube_playlist"), "YT Playlist"),
            ("tiktok_profile", _get_handler_fields("tiktok_profile"), "TikTok"),
            ("tiktok_video", _get_handler_fields("tiktok_video"), "TikTok Video"),
            ("snapchat_add", _get_handler_fields("snapchat_add"), "Snapchat"),
            ("pinterest_profile", _get_handler_fields("pinterest_profile"), "Pinterest"),
            ("reddit_profile", _get_handler_fields("reddit_profile"), "Reddit User"),
            ("reddit_subreddit", _get_handler_fields("reddit_subreddit"), "Subreddit"),
            ("tumblr_blog", _get_handler_fields("tumblr_blog"), "Tumblr"),
            ("mastodon_profile", _get_handler_fields("mastodon_profile"), "Mastodon"),
            ("threads_profile", _get_handler_fields("threads_profile"), "Threads"),
            ("bluesky_profile", _get_handler_fields("bluesky_profile"), "Bluesky"),
            ("clubhouse_profile", _get_handler_fields("clubhouse_profile"), "Clubhouse"),
            ("bereal_profile", _get_handler_fields("bereal_profile"), "BeReal"),
        ],
        "💰 Payments - India": [
            ("upi", _get_handler_fields("upi"), "UPI"),
            ("paytm", _get_handler_fields("paytm"), "Paytm"),
        ],
        "💳 Payments - Global": [
            ("paypal", _get_handler_fields("paypal"), "PayPal"),
            ("venmo", _get_handler_fields("venmo"), "Venmo"),
            ("cash_app", _get_handler_fields("cash_app"), "Cash App"),
            ("zelle", _get_handler_fields("zelle"), "Zelle"),
            ("wise", _get_handler_fields("wise"), "Wise"),
            ("revolut", _get_handler_fields("revolut"), "Revolut"),
            ("klarna", _get_handler_fields("klarna"), "Klarna"),
        ],
        "🪙 Cryptocurrency": [
            ("bitcoin", _get_handler_fields("bitcoin"), "Bitcoin"),
            ("ethereum", _get_handler_fields("ethereum"), "Ethereum"),
            ("litecoin", _get_handler_fields("litecoin"), "Litecoin"),
            ("dogecoin", _get_handler_fields("dogecoin"), "Dogecoin"),
            ("monero", _get_handler_fields("monero"), "Monero"),
            ("solana", _get_handler_fields("solana"), "Solana"),
            ("cardano", _get_handler_fields("cardano"), "Cardano"),
            ("ripple", _get_handler_fields("ripple"), "Ripple/XRP"),
            ("bnb", _get_handler_fields("bnb"), "BNB"),
            ("polygon_matic", _get_handler_fields("polygon_matic"), "Polygon"),
        ],
        "💴 Regional Payments": [
            ("alipay", _get_handler_fields("alipay"), "Alipay 🇨🇳"),
            ("wechat_pay", _get_handler_fields("wechat_pay"), "WeChat Pay 🇨🇳"),
            ("pix_brazil", _get_handler_fields("pix_brazil"), "PIX 🇧🇷"),
            ("mpesa", _get_handler_fields("mpesa"), "M-PESA 🇰🇪"),
            ("gcash", _get_handler_fields("gcash"), "GCash 🇵🇭"),
            ("grabpay", _get_handler_fields("grabpay"), "GrabPay 🇸🇬"),
            ("gopay", _get_handler_fields("gopay"), "GoPay 🇮🇩"),
            ("ovo", _get_handler_fields("ovo"), "OVO 🇮🇩"),
            ("dana", _get_handler_fields("dana"), "DANA 🇮🇩"),
            ("kakao_pay", _get_handler_fields("kakao_pay"), "Kakao Pay 🇰🇷"),
            ("line_pay", _get_handler_fields("line_pay"), "LINE Pay 🇯🇵"),
            ("paypay_japan", _get_handler_fields("paypay_japan"), "PayPay 🇯🇵"),
            ("promptpay", _get_handler_fields("promptpay"), "PromptPay 🇹🇭"),
            ("momo_vietnam", _get_handler_fields("momo_vietnam"), "MoMo 🇻🇳"),
            ("vietqr", _get_handler_fields("vietqr"), "VietQR 🇻🇳"),
        ],
        "📶 Network": [
            ("wifi", _get_handler_fields("wifi"), "WiFi Network"),
            ("wifi_eap", _get_handler_fields("wifi_eap"), "WiFi EAP"),
        ],
        "📇 Contacts": [
            ("vcard", _get_handler_fields("vcard"), "vCard"),
            ("mecard", _get_handler_fields("mecard"), "MeCard"),
            ("bizcard", _get_handler_fields("bizcard"), "BizCard"),
        ],
        "📍 Location": [
            ("geo_coordinates", _get_handler_fields("geo_coordinates"), "GPS Coords"),
            ("google_maps_search", _get_handler_fields("google_maps_search"), "Google Maps"),
            ("google_maps_directions", _get_handler_fields("google_maps_directions"), "Directions"),
            ("apple_maps_search", _get_handler_fields("apple_maps_search"), "Apple Maps"),
            ("waze_navigate", _get_handler_fields("waze_navigate"), "Waze"),
            ("what3words", _get_handler_fields("what3words"), "What3Words"),
            ("plus_code", _get_handler_fields("plus_code"), "Plus Code"),
        ],
        "🚗 Transport": [
            ("uber_ride", _get_handler_fields("uber_ride"), "Uber"),
            ("lyft_ride", _get_handler_fields("lyft_ride"), "Lyft"),
            ("grab_ride", _get_handler_fields("grab_ride"), "Grab"),
            ("ola_ride", _get_handler_fields("ola_ride"), "Ola"),
            ("didi_ride", _get_handler_fields("didi_ride"), "DiDi"),
            ("bolt_ride", _get_handler_fields("bolt_ride"), "Bolt"),
            ("airline_boarding_pass", _get_handler_fields("airline_boarding_pass"), "Boarding Pass"),
            ("train_ticket", _get_handler_fields("train_ticket"), "Train Ticket"),
        ],
        "📅 Calendar": [
            ("ical_event", _get_handler_fields("ical_event"), "iCal Event"),
            ("google_calendar_event", _get_handler_fields("google_calendar_event"), "Google Calendar"),
            ("outlook_calendar_event", _get_handler_fields("outlook_calendar_event"), "Outlook"),
        ],
        "🎵 Music & Media": [
            ("spotify_track", _get_handler_fields("spotify_track"), "Spotify Track"),
            ("spotify_playlist", _get_handler_fields("spotify_playlist"), "Spotify Playlist"),
            ("spotify_artist", _get_handler_fields("spotify_artist"), "Spotify Artist"),
            ("apple_music_url", _get_handler_fields("apple_music_url"), "Apple Music"),
            ("soundcloud_track", _get_handler_fields("soundcloud_track"), "SoundCloud"),
            ("youtube_video", _get_handler_fields("youtube_video"), "YouTube Video"),
            ("twitch_channel", _get_handler_fields("twitch_channel"), "Twitch"),
            ("netflix_title", _get_handler_fields("netflix_title"), "Netflix"),
        ],
        "🎮 Gaming": [
            ("steam_profile", _get_handler_fields("steam_profile"), "Steam Profile"),
            ("steam_game", _get_handler_fields("steam_game"), "Steam Game"),
            ("epic_games", _get_handler_fields("epic_games"), "Epic Games"),
            ("playstation_profile", _get_handler_fields("playstation_profile"), "PlayStation"),
            ("xbox_profile", _get_handler_fields("xbox_profile"), "Xbox"),
        ],
        "💻 Developer": [
            ("github_profile", _get_handler_fields("github_profile"), "GitHub Profile"),
            ("github_repo", _get_handler_fields("github_repo"), "GitHub Repo"),
            ("gitlab_project", _get_handler_fields("gitlab_project"), "GitLab"),
            ("npm_package", _get_handler_fields("npm_package"), "NPM Package"),
            ("pypi_package", _get_handler_fields("pypi_package"), "PyPI Package"),
            ("docker_hub", _get_handler_fields("docker_hub"), "Docker Hub"),
            ("notion_page", _get_handler_fields("notion_page"), "Notion"),
            ("figma_file", _get_handler_fields("figma_file"), "Figma"),
        ],
        "📱 App Stores": [
            ("google_play_app", _get_handler_fields("google_play_app"), "Google Play"),
            ("apple_app_store", _get_handler_fields("apple_app_store"), "App Store"),
            ("amazon_appstore", _get_handler_fields("amazon_appstore"), "Amazon Apps"),
            ("microsoft_store", _get_handler_fields("microsoft_store"), "MS Store"),
        ],
        "🔐 Security": [
            ("totp", _get_handler_fields("totp"), "TOTP 2FA"),
            ("hotp", _get_handler_fields("hotp"), "HOTP"),
            ("wireguard_config", _get_handler_fields("wireguard_config"), "WireGuard"),
            ("ssh_connection", _get_handler_fields("ssh_connection"), "SSH"),
        ],
        "🏠 Smart Home": [
            ("home_assistant_webhook", _get_handler_fields("home_assistant_webhook"), "Home Assistant"),
            ("homekit_setup_code", _get_handler_fields("homekit_setup_code"), "HomeKit"),
            ("matter_setup", _get_handler_fields("matter_setup"), "Matter"),
            ("mqtt_topic", _get_handler_fields("mqtt_topic"), "MQTT"),
        ],
        "🛒 Shopping": [
            ("amazon_product", _get_handler_fields("amazon_product"), "Amazon"),
            ("ebay_item", _get_handler_fields("ebay_item"), "eBay"),
            ("etsy_product", _get_handler_fields("etsy_product"), "Etsy"),
            ("shopify_product", _get_handler_fields("shopify_product"), "Shopify"),
            ("flipkart_product", _get_handler_fields("flipkart_product"), "Flipkart"),
            ("product_barcode", _get_handler_fields("product_barcode"), "Barcode"),
        ],
        "🍔 Food Delivery": [
            ("ubereats_restaurant", _get_handler_fields("ubereats_restaurant"), "Uber Eats"),
            ("doordash_restaurant", _get_handler_fields("doordash_restaurant"), "DoorDash"),
            ("zomato_restaurant", _get_handler_fields("zomato_restaurant"), "Zomato"),
            ("swiggy_restaurant", _get_handler_fields("swiggy_restaurant"), "Swiggy"),
            ("yelp_business", _get_handler_fields("yelp_business"), "Yelp"),
        ],
        "🏨 Travel": [
            ("booking_com", _get_handler_fields("booking_com"), "Booking.com"),
            ("airbnb_listing", _get_handler_fields("airbnb_listing"), "Airbnb"),
            ("tripadvisor", _get_handler_fields("tripadvisor"), "TripAdvisor"),
        ],
        "💼 Jobs": [
            ("indeed_job", _get_handler_fields("indeed_job"), "Indeed"),
            ("linkedin_profile", _get_handler_fields("linkedin_profile"), "LinkedIn"),
            ("upwork_profile", _get_handler_fields("upwork_profile"), "Upwork"),
            ("fiverr_gig", _get_handler_fields("fiverr_gig"), "Fiverr"),
        ],
        "🎓 Education": [
            ("coursera_course", _get_handler_fields("coursera_course"), "Coursera"),
            ("udemy_course", _get_handler_fields("udemy_course"), "Udemy"),
            ("duolingo_profile", _get_handler_fields("duolingo_profile"), "Duolingo"),
            ("google_classroom", _get_handler_fields("google_classroom"), "Google Classroom"),
            ("student_id", _get_handler_fields("student_id"), "Student ID"),
        ],
        "🏥 Health": [
            ("medical_record_id", _get_handler_fields("medical_record_id"), "Medical Record"),
            ("prescription", _get_handler_fields("prescription"), "Prescription"),
            ("health_insurance_card", _get_handler_fields("health_insurance_card"), "Insurance"),
            ("covid_vaccine_cert", _get_handler_fields("covid_vaccine_cert"), "Vaccine Cert"),
        ],
        "🎫 Events & Tickets": [
            ("eventbrite_event", _get_handler_fields("eventbrite_event"), "Eventbrite"),
            ("ticketmaster_event", _get_handler_fields("ticketmaster_event"), "Ticketmaster"),
            ("meetup_event", _get_handler_fields("meetup_event"), "Meetup"),
            ("movie_ticket", _get_handler_fields("movie_ticket"), "Movie Ticket"),
            ("concert_ticket", _get_handler_fields("concert_ticket"), "Concert"),
            ("sports_ticket", _get_handler_fields("sports_ticket"), "Sports"),
        ],
        "🎧 Podcasts": [
            ("apple_podcasts", _get_handler_fields("apple_podcasts"), "Apple Podcasts"),
            ("spotify_podcast", _get_handler_fields("spotify_podcast"), "Spotify Podcast"),
            ("google_podcasts", _get_handler_fields("google_podcasts"), "Google Podcasts"),
            ("podcast_rss", _get_handler_fields("podcast_rss"), "Podcast RSS"),
        ],
        "📰 News & Content": [
            ("medium_article", _get_handler_fields("medium_article"), "Medium"),
            ("substack_newsletter", _get_handler_fields("substack_newsletter"), "Substack"),
            ("wikipedia", _get_handler_fields("wikipedia"), "Wikipedia"),
            ("arxiv_paper", _get_handler_fields("arxiv_paper"), "arXiv"),
            ("doi", _get_handler_fields("doi"), "DOI"),
            ("isbn", _get_handler_fields("isbn"), "ISBN"),
        ],
        "🔗 NFT & Web3": [
            ("opensea_nft", _get_handler_fields("opensea_nft"), "OpenSea"),
            ("metamask_connect", _get_handler_fields("metamask_connect"), "MetaMask"),
            ("walletconnect", _get_handler_fields("walletconnect"), "WalletConnect"),
            ("ens_domain", _get_handler_fields("ens_domain"), "ENS Domain"),
            ("ipfs_gateway", _get_handler_fields("ipfs_gateway"), "IPFS"),
            ("etherscan_address", _get_handler_fields("etherscan_address"), "Etherscan"),
        ],
        "🌏 Asian Social": [
            ("wechat_profile", _get_handler_fields("wechat_profile"), "WeChat 🇨🇳"),
            ("weibo", _get_handler_fields("weibo"), "Weibo 🇨🇳"),
            ("douyin", _get_handler_fields("douyin"), "Douyin 🇨🇳"),
            ("bilibili", _get_handler_fields("bilibili"), "Bilibili 🇨🇳"),
            ("qq", _get_handler_fields("qq"), "QQ 🇨🇳"),
            ("line_profile", _get_handler_fields("line_profile"), "LINE 🇯🇵"),
            ("kakaotalk", _get_handler_fields("kakaotalk"), "KakaoTalk 🇰🇷"),
            ("zalo", _get_handler_fields("zalo"), "Zalo 🇻🇳"),
            ("vk", _get_handler_fields("vk"), "VK 🇷🇺"),
        ],
        "🏪 Loyalty & Membership": [
            ("loyalty_card", _get_handler_fields("loyalty_card"), "Loyalty Card"),
            ("gym_membership", _get_handler_fields("gym_membership"), "Gym"),
            ("library_card", _get_handler_fields("library_card"), "Library"),
            ("costco_membership", _get_handler_fields("costco_membership"), "Costco"),
            ("amazon_prime", _get_handler_fields("amazon_prime"), "Prime"),
        ],
        "📜 Plain Data": [
            ("plain_text", _get_handler_fields("plain_text"), "Plain Text"),
            ("json_data", _get_handler_fields("json_data"), "JSON Data"),
            ("base64_data", _get_handler_fields("base64_data"), "Base64"),
            ("google_search", _get_handler_fields("google_search"), "Google Search"),
        ],
    }
except Exception as e:
    # Fallback minimal handlers if import fails
    print(f"[QRPanel] Warning: Could not load handlers dynamically: {e}")
    HANDLER_CATEGORIES = {
        "🌐 Web": [("url", ["url"], "URL")],
        "📰 Content": [("plain_text", ["text"], "Plain Text")],
    }

# Flatten for lookup
ALL_HANDLERS = {}
for category, handlers in HANDLER_CATEGORIES.items():
    for handler_name, fields, description in handlers:
        ALL_HANDLERS[handler_name] = {"fields": fields, "description": description, "category": category}

# Options
GRADIENT_MASKS = ["radial", "horizontal", "vertical", "diagonal"]
MODULE_DRAWERS = ["rounded", "square", "circle", "gapped"]


class ColorPickerButton(QPushButton):
    """Compact color picker button with label."""
    
    color_changed = pyqtSignal(str)
    
    def __init__(self, label: str, initial_color: str = "#ffffff"):
        super().__init__()
        self._color = initial_color
        self._label = label
        self.setFixedHeight(32)
        self.setMinimumWidth(80)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()
        self.clicked.connect(self._pick_color)
    
    def _update_style(self):
        # Determine text color based on background brightness
        r, g, b = int(self._color[1:3], 16), int(self._color[3:5], 16), int(self._color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "#000" if brightness > 128 else "#fff"
        
        self.setText(f"{self._label}")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {text_color};
                border: 2px solid #444;
                border-radius: 6px;
                font-family: Consolas;
                font-size: 10px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                border-color: {PINK};
            }}
        """)
    
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, f"Select {self._label}")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)
    
    def get_color(self) -> str:
        return self._color
    
    def set_color(self, color: str):
        self._color = color
        self._update_style()


class QRPanel(QWidget):
    """Clean, aligned QR panel."""
    
    generate_requested = pyqtSignal(str, dict, str, bool, list, str, str, str, str)
    # handler, data, mode, auto_mode, colors[3], mask, drawer, logo_path, prompt
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 0)
        main_layout.setSpacing(0)
        
        # Container frame
        self.container = QFrame()
        self.container.setObjectName("QRContainer")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # === ROW 1: Title ===
        self.title_label = QLabel("📱 QR STUDIO")
        self.title_label.setObjectName("title")
        self.title_label.setFont(QFont("Consolas", 15, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        # === ROW 2: Handler Search + Dropdown ===
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        
        self.handler_label = QLabel("Handler")
        self.handler_label.setFixedWidth(60)
        row2.addWidget(self.handler_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.setFixedWidth(120)
        self.search_input.textChanged.connect(self._filter_handlers)
        row2.addWidget(self.search_input)
        
        self.handler_combo = QComboBox()
        self.handler_combo.setMaxVisibleItems(12)
        self._populate_handlers()
        self.handler_combo.currentTextChanged.connect(self._on_handler_changed)
        row2.addWidget(self.handler_combo, 1)
        
        layout.addLayout(row2)
        
        # === ROW 3: Data Input Fields ===
        data_row_label = QHBoxLayout()
        self.data_label = QLabel("Data")
        self.data_label.setFixedWidth(55)
        data_row_label.addWidget(self.data_label)
        
        self.data_hint = QLabel("← Enter your QR data in the fields below")
        self.data_hint.setObjectName("hint")
        data_row_label.addWidget(self.data_hint)
        data_row_label.addStretch()
        layout.addLayout(data_row_label)
        
        self.fields_frame = QFrame()
        self.fields_layout = QGridLayout(self.fields_frame)
        self.fields_layout.setContentsMargins(10, 8, 10, 8)
        self.fields_layout.setSpacing(8)
        self.fields_layout.setColumnStretch(1, 1)
        self.fields_layout.setColumnStretch(3, 1)
        
        self.fields_scroll = QScrollArea()
        self.fields_scroll.setWidgetResizable(True)
        self.fields_scroll.setMinimumHeight(60)
        self.fields_scroll.setMaximumHeight(120)
        self.fields_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.fields_scroll.setWidget(self.fields_frame)
        layout.addWidget(self.fields_scroll)
        
        self.field_inputs = {}
        
        # === ROW 4: Output Mode ===
        row4 = QHBoxLayout()
        row4.setSpacing(10)
        
        self.output_label = QLabel("Output")
        self.output_label.setFixedWidth(55)
        row4.addWidget(self.output_label)
        
        # Mode dropdown instead of buttons (prevents overlap)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["📄 SVG", "🌈 Gradient", "✨ Creative"])
        self.mode_combo.setFixedWidth(140)
        self.mode_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        row4.addWidget(self.mode_combo)
        
        row4.addStretch()
        layout.addLayout(row4)
        
        # === ROW 4b: Creative Mode Options ===
        self.creative_frame = QFrame()
        creative_layout = QVBoxLayout(self.creative_frame)
        creative_layout.setContentsMargins(0, 5, 0, 0)
        creative_layout.setSpacing(8)
        
        # Prompt input row
        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(10)
        
        self.prompt_label = QLabel("Prompt")
        self.prompt_label.setFixedWidth(55)
        prompt_row.addWidget(self.prompt_label)
        
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("e.g. forest theme, cyberpunk neon, galaxy space...")
        prompt_row.addWidget(self.prompt_input, 1)
        
        creative_layout.addLayout(prompt_row)
        
        # Hint text
        hint_row = QHBoxLayout()
        hint_spacer = QLabel("")
        hint_spacer.setFixedWidth(55)
        hint_row.addWidget(hint_spacer)
        
        self.creative_hint = QLabel("💡 AI will enhance your prompt with proven styles from 96 templates")
        self.creative_hint.setObjectName("hint")
        hint_row.addWidget(self.creative_hint)
        hint_row.addStretch()
        creative_layout.addLayout(hint_row)
        
        self.creative_frame.hide()
        layout.addWidget(self.creative_frame)
        
        # === ROW 5: Gradient Options ===
        self.gradient_frame = QFrame()
        grad_layout = QVBoxLayout(self.gradient_frame)
        grad_layout.setContentsMargins(0, 5, 0, 0)
        grad_layout.setSpacing(8)
        
        # Sub-row 5a: Auto/Manual toggle
        row5a = QHBoxLayout()
        row5a.setSpacing(10)
        
        self.colors_label = QLabel("Colors")
        self.colors_label.setFixedWidth(55)
        row5a.addWidget(self.colors_label)
        
        self.auto_radio = QRadioButton("🎲 Random")
        self.auto_radio.setChecked(True)
        self.auto_radio.toggled.connect(self._on_color_mode_changed)
        row5a.addWidget(self.auto_radio)
        
        self.manual_radio = QRadioButton("🎨 Manual")
        row5a.addWidget(self.manual_radio)
        
        row5a.addStretch()
        grad_layout.addLayout(row5a)
        
        # Sub-row 5b: Color pickers
        self.color_row = QHBoxLayout()
        self.color_row.setSpacing(8)
        
        spacer = QLabel("")
        spacer.setFixedWidth(55)
        self.color_row.addWidget(spacer)
        
        self.color_back = ColorPickerButton("Background", "#ffffff")
        self.color_row.addWidget(self.color_back)
        
        self.color_first = ColorPickerButton("First", "#ff5500")
        self.color_row.addWidget(self.color_first)
        
        self.color_second = ColorPickerButton("Second", "#0055ff")
        self.color_row.addWidget(self.color_second)
        
        self.color_row.addStretch()
        
        self.color_widget = QWidget()
        self.color_widget.setLayout(self.color_row)
        self.color_widget.hide()
        grad_layout.addWidget(self.color_widget)
        
        # Sub-row 5c: Mask + Drawer
        row5c = QHBoxLayout()
        row5c.setSpacing(10)
        
        self.style_label = QLabel("Style")
        self.style_label.setFixedWidth(55)
        row5c.addWidget(self.style_label)
        
        self.mask_combo = QComboBox()
        self.mask_combo.addItems(GRADIENT_MASKS)
        self.mask_combo.setFixedWidth(100)
        row5c.addWidget(self.mask_combo)
        
        self.drawer_combo = QComboBox()
        self.drawer_combo.addItems(MODULE_DRAWERS)
        self.drawer_combo.setFixedWidth(100)
        row5c.addWidget(self.drawer_combo)
        
        row5c.addStretch()
        grad_layout.addLayout(row5c)
        
        self.gradient_frame.hide()
        layout.addWidget(self.gradient_frame)
        
        # === ROW 6: Logo ===
        self.logo_widget = QWidget()
        logo_layout = QHBoxLayout(self.logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(10)
        
        self.logo_label = QLabel("Logo")
        self.logo_label.setFixedWidth(55)
        logo_layout.addWidget(self.logo_label)
        
        self.logo_input = QLineEdit()
        self.logo_input.setPlaceholderText("Optional: path/to/logo.png")
        logo_layout.addWidget(self.logo_input, 1)
        
        self.browse_logo_btn = QPushButton("📂")
        self.browse_logo_btn.setFixedSize(30, 26)
        self.browse_logo_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.browse_logo_btn.clicked.connect(self._browse_logo)
        logo_layout.addWidget(self.browse_logo_btn)
        
        self.logo_widget.hide()
        layout.addWidget(self.logo_widget)
        
        # === ROW 7: Generate Button ===
        row7 = QHBoxLayout()
        row7.setContentsMargins(0, 8, 0, 0)
        row7.addStretch()
        
        self.generate_btn = QPushButton("⚡ Generate QR Code")
        self.generate_btn.setFixedSize(180, 36)
        self.generate_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.generate_btn.clicked.connect(self._on_generate)
        row7.addWidget(self.generate_btn)
        row7.addStretch()
        
        layout.addLayout(row7)
        main_layout.addWidget(self.container)
        
        # Initial Styling
        self.update_theme()
        
        # Initialize handler fields
        self._on_handler_changed(self.handler_combo.currentText())

    def update_theme(self):
        """Update widget styling based on current theme."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        print(f"[QRPanel] update_theme: is_dark={is_dark}, theme={theme.name}")
        
        if is_dark:
            bg_color = "#0d0d14"
            border_color = "#2a2a3a"
            text_color = "#999"
            field_bg = "#12121a"
            radio_color = "#ccc"
            radio_border = "#555"
            radio_bg = "#1a1a2e"
        else:
            bg_color = "rgba(255, 255, 255, 0.95)"
            border_color = "#e0e0e0"
            text_color = "#666"
            field_bg = "#f9f9fc"
            radio_color = "#444"
            radio_border = "#bbb"
            radio_bg = "#ffffff"

        # Container
        self.container.setStyleSheet(f"""
            QFrame#QRContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        # Labels
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 11px;
                font-family: Consolas;
                border: none;
            }}
            QLabel#title {{
                color: {PINK};
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QLabel#hint {{
                color: {text_color};
                font-size: 9px;
                font-style: italic;
            }}
        """)
        
        # Fields Frame
        self.fields_frame.setStyleSheet(f"""
            background: {field_bg};
            border: 1px solid {border_color};
            border-radius: 8px;
        """)
        
        # Scroll Area
        self.fields_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ width: 4px; background: {bg_color}; }}
            QScrollBar::handle:vertical {{ background: {border_color}; border-radius: 2px; }}
        """)
        
        # Radios
        radio_style = f"""
            QRadioButton {{
                color: {radio_color}; font-size: 10px; border: none; outline: none;
            }}
            QRadioButton::indicator {{
                width: 14px; height: 14px;
                border-radius: 7px;
                border: 1px solid {radio_border};
                background: {radio_bg};
            }}
            QRadioButton::indicator:checked {{
                border: 1px solid {PINK};
                background: {PINK};
            }}
            QRadioButton::indicator:unchecked:hover {{
                border-color: {PINK};
            }}
        """
        self.auto_radio.setStyleSheet(radio_style)
        self.manual_radio.setStyleSheet(radio_style)

        # Inputs and Combos rely on helper methods that check theme dynamicly or we set them here
        self.search_input.setStyleSheet(self._input_style())
        self.handler_combo.setStyleSheet(self._combo_style())
        self.mode_combo.setStyleSheet(self._combo_style())
        self.mask_combo.setStyleSheet(self._combo_style())
        self.drawer_combo.setStyleSheet(self._combo_style())
        self.logo_input.setStyleSheet(self._input_style())
        self.prompt_input.setStyleSheet(self._input_style())
        
        # Gradient Frame specific
        self.gradient_frame.setStyleSheet("background: transparent; border: none;")
        
        # Creative Frame specific
        self.creative_frame.setStyleSheet("background: transparent; border: none;")
        
        # Browse Button
        self.browse_logo_btn.setStyleSheet(f"""
            QPushButton {{
                background: {field_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
            }}
            QPushButton:hover {{
                border-color: {PINK};
            }}
        """)
        
        # Generate Button always vibrant
        self.generate_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                color: white; border: none; border-radius: 18px;
                font-family: Consolas; font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #9b4fc9, stop:0.5 #f04080, stop:1 #ff9050); }}
            QPushButton:disabled {{ background: #333; color: #666; }}
        """)

    def _input_style(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if is_dark:
            bg = "#1a1a2e"
            color = "#fff"
            border = "#444"
            focus_bg = "#1f1f35"
        else:
            bg = "#ffffff"
            color = "#000"
            border = "#ddd"
            focus_bg = "#fafafa"
            
        return f"""QLineEdit {{ 
            background: {bg}; color: {color}; border: 1px solid {border}; 
            border-radius: 6px; padding: 6px 10px; 
            font-family: Consolas; font-size: 11px; 
        }} 
        QLineEdit:hover {{ border-color: #999; }}
        QLineEdit:focus {{ border-color: {PINK}; background: {focus_bg}; }}"""
    
    def _combo_style(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if is_dark:
            bg = "#1a1a2e"
            color = "#fff"
            border = "#444"
            sel_bg = "#1a1a2e"
        else:
            bg = "#ffffff"
            color = "#000"
            border = "#ddd"
            sel_bg = "#ffffff"
            
        return f"""QComboBox {{ 
            background: {bg}; color: {color}; border: 1px solid {border}; 
            border-radius: 6px; padding: 6px 10px; 
            font-family: Consolas; font-size: 11px; 
        }} 
        QComboBox:hover {{ border-color: #999; }}
        QComboBox:focus {{ border-color: {PINK}; }} 
        QComboBox::drop-down {{ border: none; width: 20px; }} 
        QComboBox::down-arrow {{ border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #888; }} 
        QComboBox QAbstractItemView {{ background: {sel_bg}; color: {color}; selection-background-color: {PINK}; selection-color: white; border: 1px solid {border}; font-size: 11px; }}"""
    
    def _populate_handlers(self, filter_text: str = ""):
        """Populate handler dropdown, optionally filtered."""
        self.handler_combo.blockSignals(True)
        old_text = self.handler_combo.currentText()
        self.handler_combo.clear()
        
        flt = filter_text.lower()
        for cat, handlers in HANDLER_CATEGORIES.items():
            matches = [(n, d) for n, _, d in handlers if flt in n.lower() or flt in d.lower()]
            if matches:
                self.handler_combo.addItem(f"── {cat} ──")
                self.handler_combo.model().item(self.handler_combo.count() - 1).setEnabled(False)
                for name, desc in matches:
                    self.handler_combo.addItem(f"{name} - {desc}")
        
        # Try to restore selection or select first valid
        if old_text:
            idx = self.handler_combo.findText(old_text)
            if idx >= 0:
                self.handler_combo.setCurrentIndex(idx)
            else:
                self.handler_combo.setCurrentIndex(self._first_valid_index())
        else:
            self.handler_combo.setCurrentIndex(self._first_valid_index())
        
        self.handler_combo.blockSignals(False)
        
        # If selection changed, manually trigger handler update (only if fields_layout exists)
        new_text = self.handler_combo.currentText()
        if new_text != old_text and hasattr(self, 'fields_layout'):
            self._on_handler_changed(new_text)
    
    def _first_valid_index(self):
        for i in range(self.handler_combo.count()):
            if self.handler_combo.model().item(i).isEnabled():
                return i
        return 0
    
    def _filter_handlers(self, text):
        self._populate_handlers(text)
    
    def _on_handler_changed(self, text):
        if not text or text.startswith("──"):
            return
        
        handler = text.split(" - ")[0].strip()
        if handler not in ALL_HANDLERS:
            return
        
        fields = ALL_HANDLERS[handler]["fields"]
        
        # Clear old widgets completely
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        self.field_inputs = {}
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        default_label_color = "#bbb" if is_dark else "#666"
        
        # Create 2-column grid with new fields
        for i, fname in enumerate(fields[:20]):
            row, col = i // 2, (i % 2) * 2
            
            # First field is required, mark with red color
            is_required = (i == 0)
            lbl = QLabel(f"{fname}:")
            color = "#ff6b6b" if is_required else default_label_color
            lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-family: Consolas; border: none;")
            lbl.setFixedWidth(80)
            self.fields_layout.addWidget(lbl, row, col)
            
            inp = QLineEdit()
            inp.setPlaceholderText(f"{'REQUIRED' if is_required else fname}")
            inp.setStyleSheet(self._input_style())
            self.fields_layout.addWidget(inp, row, col + 1)
            self.field_inputs[fname] = inp
    
    def _set_mode(self, mode):
        """Set mode programmatically (for internal use)."""
        index_map = {"svg": 0, "gradient": 1, "creative": 2}
        if mode in index_map:
            self.mode_combo.setCurrentIndex(index_map[mode])
    
    def _on_mode_changed(self, text):
        """Handle mode dropdown change."""
        if "SVG" in text:
            mode = "svg"
        elif "Gradient" in text:
            mode = "gradient"
        else:
            mode = "creative"
        
        self.gradient_frame.setVisible(mode == "gradient")
        self.creative_frame.setVisible(mode == "creative")
        self.logo_widget.setVisible(mode == "gradient")  # Logo only for gradient
    
    def _on_color_mode_changed(self):
        self.color_widget.setVisible(self.manual_radio.isChecked())
    
    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.svg);;All (*)")
        if path:
            self.logo_input.setText(path)
    
    def _on_generate(self):
        text = self.handler_combo.currentText()
        if not text or text.startswith("──"):
            return
        
        handler = text.split(" - ")[0].strip()
        
        # Get handler info for required fields
        handler_info = ALL_HANDLERS.get(handler, {})
        required_fields = handler_info.get("fields", [])
        
        # Build data dict - check required fields
        data = {}
        first_field_filled = False
        for fname in required_fields:
            inp = self.field_inputs.get(fname)
            if inp:
                val = inp.text().strip()
                if val:
                    data[fname] = val
                    first_field_filled = True
                else:
                    # Use placeholder value for empty optional fields
                    data[fname] = ""
        
        # The FIRST field is always required - validate it
        if required_fields:
            first_field = required_fields[0]
            first_input = self.field_inputs.get(first_field)
            if first_input and not first_input.text().strip():
                # Show shake animation
                self._shake_widget(first_input)
                
                # Flash red border
                original_style = first_input.styleSheet()
                first_input.setStyleSheet(original_style + " QLineEdit { border: 2px solid #ff4444 !important; }")
                
                # Show tooltip
                from PyQt6.QtWidgets import QToolTip
                from PyQt6.QtCore import QPoint, QTimer
                pos = first_input.mapToGlobal(QPoint(0, first_input.height()))
                QToolTip.showText(pos, f"⚠️ {first_field} is required!", first_input, first_input.rect(), 3000)
                
                # Reset border after 1 second
                QTimer.singleShot(1000, lambda: first_input.setStyleSheet(self._input_style()))
                return
        
        # Determine mode from dropdown
        mode_text = self.mode_combo.currentText()
        if "SVG" in mode_text:
            mode = "svg"
        elif "Gradient" in mode_text:
            mode = "gradient"
        else:
            mode = "creative"
        
        auto_mode = self.auto_radio.isChecked()
        colors = [self.color_back.get_color(), self.color_first.get_color(), self.color_second.get_color()]
        mask = self.mask_combo.currentText()
        drawer = self.drawer_combo.currentText()
        logo = self.logo_input.text().strip()
        prompt = self.prompt_input.text().strip() if mode == "creative" else ""
        
        self.generate_requested.emit(handler, data, mode, auto_mode, colors, mask, drawer, logo, prompt)
    
    def set_enabled(self, enabled: bool):
        self.handler_combo.setEnabled(enabled)
        self.search_input.setEnabled(enabled)
        self.mode_combo.setEnabled(enabled)
        self.generate_btn.setEnabled(enabled)
        self.logo_input.setEnabled(enabled)
        self.prompt_input.setEnabled(enabled)
        for inp in self.field_inputs.values():
            inp.setEnabled(enabled)
    
    def _shake_widget(self, widget):
        """Shake animation for invalid input."""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
        
        # Get original position
        original_pos = widget.pos()
        
        # Create animation
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(300)
        anim.setLoopCount(1)
        
        # Keyframes for shake effect
        anim.setKeyValueAt(0, original_pos)
        anim.setKeyValueAt(0.1, original_pos + QPoint(8, 0))
        anim.setKeyValueAt(0.2, original_pos + QPoint(-8, 0))
        anim.setKeyValueAt(0.3, original_pos + QPoint(6, 0))
        anim.setKeyValueAt(0.4, original_pos + QPoint(-6, 0))
        anim.setKeyValueAt(0.5, original_pos + QPoint(4, 0))
        anim.setKeyValueAt(0.6, original_pos + QPoint(-4, 0))
        anim.setKeyValueAt(0.7, original_pos + QPoint(2, 0))
        anim.setKeyValueAt(0.8, original_pos + QPoint(-2, 0))
        anim.setKeyValueAt(1, original_pos)
        
        anim.setEasingCurve(QEasingCurve.Type.Linear)
        
        # Store ref to prevent garbage collection
        self._shake_anim = anim
        anim.start()
