"""
InstaTrace Configuration — API endpoints, user agents, constants, and color theme.
Author: John-Varghese-EH
"""

import random
from colorama import Fore, Back, Style, init

init(autoreset=True)


# ═══════════════════════ COLOR THEME ═══════════════════════

class Colors:
    """Terminal color presets for the InstaTrace CLI."""
    BRAND      = Fore.MAGENTA + Style.BRIGHT
    SUCCESS    = Fore.GREEN + Style.BRIGHT
    INFO       = Fore.CYAN
    WARNING    = Fore.YELLOW + Style.BRIGHT
    ERROR      = Fore.RED + Style.BRIGHT
    DIM        = Fore.LIGHTBLACK_EX
    WHITE      = Fore.WHITE + Style.BRIGHT
    BLUE       = Fore.BLUE + Style.BRIGHT
    HEADER     = Fore.CYAN + Style.BRIGHT
    VALUE      = Fore.WHITE
    LABEL      = Fore.LIGHTYELLOW_EX
    SEPARATOR  = Fore.LIGHTBLACK_EX
    RESET      = Style.RESET_ALL
    ACCENT     = Fore.LIGHTMAGENTA_EX + Style.BRIGHT
    LINK       = Fore.LIGHTCYAN_EX + Style.BRIGHT


C = Colors  # Shorthand


# ═══════════════════════ BANNER ═══════════════════════

BANNER = f"""
{C.BRAND}
    ██╗███╗   ██╗███████╗████████╗ █████╗ ████████╗██████╗  █████╗  ██████╗███████╗
    ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
    ██║██╔██╗ ██║███████╗   ██║   ███████║   ██║   ██████╔╝███████║██║     █████╗  
    ██║██║╚██╗██║╚════██║   ██║   ██╔══██║   ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
    ██║██║ ╚████║███████║   ██║   ██║  ██║   ██║   ██║  ██║██║  ██║╚██████╗███████╗
    ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
{C.RESET}
{C.ACCENT}    ⚡ Ultimate Instagram OSINT Intelligence Tool v1.0.0{C.RESET}
{C.DIM}    ─────────────────────────────────────────────────────────────────────────────
{C.LABEL}    Author  : {C.VALUE}John-Varghese-EH{C.RESET}
{C.LABEL}    GitHub  : {C.LINK}https://github.com/John-Varghese-EH/InstaTrace{C.RESET}
{C.LABEL}    License : {C.VALUE}GPL-3.0{C.RESET}
{C.DIM}    ─────────────────────────────────────────────────────────────────────────────{C.RESET}
{C.WARNING}    ⚠  For authorized security research & educational use only{C.RESET}
"""


# ═══════════════════════ USER AGENTS ═══════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Instagram 121.0.0.29.119 Android (26/8.0.0; 480dpi; 1080x2032; "
    "HUAWEI; FIG-LX1; HWFIG-H; hi6250; en_US; 185203708)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 "
    "(KHTML, like Gecko) Mobile/14G60 Instagram 12.0.0.16.90 "
    "(iPhone9,4; iOS 10_3_3; en_US; en-US; scale=2.61; gamut=wide; 1080x1920)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Instagram 275.0.0.27.98 Android (33/13; 420dpi; 1080x2340; "
    "samsung; SM-A546B; a54x; exynos1380; en_US; 458229237)",
]


def random_ua():
    """Return a random User-Agent string."""
    return random.choice(USER_AGENTS)


# ═══════════════════════ API ENDPOINTS ═══════════════════════

BASE_URL = "https://www.instagram.com/"
LOGIN_URL = "https://www.instagram.com/accounts/login/ajax/"
GRAPHQL_URL = "https://www.instagram.com/graphql/query/"

# Instagram Private API (i.instagram.com)
USER_INFO_ENDPOINT       = "https://i.instagram.com/api/v1/users/{}/info/"
USER_PROFILE_ENDPOINT    = "https://www.instagram.com/api/v1/users/web_profile_info/?username={}"
USER_SEARCH_ENDPOINT     = "https://www.instagram.com/web/search/topsearch/?query={}"
USER_FOLLOWERS_ENDPOINT  = "https://i.instagram.com/api/v1/friendships/{}/followers/"
USER_FOLLOWINGS_ENDPOINT = "https://i.instagram.com/api/v1/friendships/{}/following/"
STORY_ENDPOINT           = "https://i.instagram.com/api/v1/feed/reels_media/?reel_ids={}"
HIGHLIGHTS_ENDPOINT      = "https://i.instagram.com/api/v1/highlights/{}/highlights_tray/"
STORY_HIGHLIGHTS_ENDPOINT = "https://i.instagram.com/api/v1/feed/reels_media/?reel_ids={}"
TAGGED_ENDPOINT          = "https://i.instagram.com/api/v1/usertags/{}/feed/"
COMMENTS_ENDPOINT        = "https://i.instagram.com/api/v1/media/{}/comments/"
SIMILAR_ACCOUNTS_ENDPOINT = "https://i.instagram.com/api/v1/discover/chaining/?target_id={}"
LOCATION_SEARCH_ENDPOINT = "https://www.instagram.com/api/v1/locations/web_info/"
ABOUT_USER_URL           = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.interactions.about_this_account/"
USER_LOOKUP_URL          = "https://i.instagram.com/api/v1/users/lookup/"

# GraphQL Query Hashes
POST_DETAILS_QUERY    = "9f8827793ef34641b2fb195d4d41151c"
USER_FEED_QUERY       = "69cba40317214236af40e7efa697781d"
FOLLOWERS_LIST_QUERY  = "7dd9a7e2160524fd85f50317462cff9f"
FOLLOWING_LIST_QUERY  = "c56ee0ae1f89cdbd1c89e2bc6b8f3d18"
HASHTAG_QUERY         = "9b498c08113f1e09617a1703c22b2f32"
ABOUT_USER_QUERY      = "8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb"


# ═══════════════════════ SETTINGS ═══════════════════════

MAX_RETRIES = 3
REQUEST_TIMEOUT = 10
MIN_SESSION_REQUESTS = 3
MAX_SESSION_REQUESTS = 6
PROXY = None  # e.g. {"http": "socks5://...", "https": "socks5://..."}

# App IDs
IG_APP_ID = "936619743392459"
IG_APP_ID_ALT = "124024574287414"


# ═══════════════════════ HELPERS ═══════════════════════

def print_status(msg, level="info"):
    """Print a color-coded status message."""
    icons = {"success": "✓", "info": "→", "warning": "⚠", "error": "✗", "dim": "·"}
    colors = {
        "success": C.SUCCESS, "info": C.INFO, "warning": C.WARNING,
        "error": C.ERROR, "dim": C.DIM
    }
    icon = icons.get(level, "→")
    color = colors.get(level, C.INFO)
    print(f"  {color}{icon} {msg}{C.RESET}")


def print_field(label, value, label_width=28):
    """Print a formatted label: value pair."""
    if value is None or value == "" or value == "None":
        return
    print(f"  {C.LABEL}{'│'} {label:<{label_width}}{C.VALUE}{value}{C.RESET}")


def print_separator(char="─", width=72):
    """Print a visual separator line."""
    print(f"  {C.SEPARATOR}{char * width}{C.RESET}")


def print_section(title):
    """Print a section header."""
    print()
    print(f"  {C.HEADER}┌{'─' * 70}┐{C.RESET}")
    print(f"  {C.HEADER}│ {C.ACCENT}{'▸ ' + title:<69}{C.HEADER}│{C.RESET}")
    print(f"  {C.HEADER}└{'─' * 70}┘{C.RESET}")


def bool_icon(val):
    """Return a colored boolean indicator."""
    if val:
        return f"{C.SUCCESS}● Yes{C.RESET}"
    return f"{C.ERROR}○ No{C.RESET}"
