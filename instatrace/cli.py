"""
InstaTrace CLI — Rich command-line interface with sub-commands.
Author: John-Varghese-EH
"""

import argparse
import sys
from . import __version__
from .config import BANNER, C, print_status, print_separator
from .api import InstaAPI


def create_parser():
    """Build the argument parser with all sub-commands."""
    parser = argparse.ArgumentParser(
        prog="instatrace",
        description="InstaTrace — Ultimate Instagram OSINT Intelligence Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{C.ACCENT}Examples:{C.RESET}
  instatrace profile -u johndoe -s SESSION_ID
  instatrace profile -u johndoe -s SESSION_ID --export json
  instatrace lookup -u johndoe
  instatrace posts -u johndoe -s SESSION_ID --total 20
  instatrace post-info -p https://instagram.com/p/ABC123 -s SESSION_ID
  instatrace followers -u johndoe -s SESSION_ID --total 500
  instatrace following -u johndoe -s SESSION_ID
  instatrace mutual -u user1 -u2 user2 -s SESSION_ID
  instatrace hashtag -t photography -s SESSION_ID
  instatrace similar -u johndoe -s SESSION_ID
  instatrace highlights -u johndoe -s SESSION_ID
  instatrace tagged -u johndoe -s SESSION_ID
  instatrace comments -m 12345678 -s SESSION_ID
  instatrace check -u johndoe
  instatrace biolink --url https://example.com
  instatrace ratio -u johndoe -s SESSION_ID

{C.DIM}Author: John-Varghese-EH | github.com/John-Varghese-EH/InstaTrace{C.RESET}
        """,
    )
    parser.add_argument("-v", "--version", action="version", version=f"InstaTrace v{__version__}")

    sub = parser.add_subparsers(dest="command", title="Commands", metavar="")

    # ── Session args (shared) ──
    def add_session(p):
        p.add_argument("-s", "--session-id", help="Instagram session ID cookie", default=None)
        p.add_argument("--sessions", nargs="+", help="Multiple session IDs for rotation", default=None)
        p.add_argument("--proxy", help='Proxy URL, e.g. socks5://127.0.0.1:9050', default=None)
        p.add_argument("--export", choices=["json", "csv", "txt"], help="Export results to file", default=None)

    # 1. PROFILE
    p_prof = sub.add_parser("profile", help="Full profile intelligence for a user", aliases=["p"])
    p_prof.add_argument("-u", "--username", required=True, help="Instagram username")
    add_session(p_prof)

    # 2. LOOKUP
    p_lookup = sub.add_parser("lookup", help="Advanced lookup (obfuscated email/phone)", aliases=["l"])
    p_lookup.add_argument("-u", "--username", required=True, help="Instagram username")
    add_session(p_lookup)

    # 3. POSTS
    p_posts = sub.add_parser("posts", help="Extract user's posts/media", aliases=["m"])
    p_posts.add_argument("-u", "--username", required=True, help="Instagram username")
    p_posts.add_argument("--total", type=int, default=20, help="Max posts to fetch (default: 20)")
    p_posts.add_argument("--from-date", help="Start date filter (YYYY-MM-DD)")
    p_posts.add_argument("--to-date", help="End date filter (YYYY-MM-DD)")
    p_posts.add_argument("--show-urls", action="store_true", help="Show media URLs")
    add_session(p_posts)

    # 4. POST INFO
    p_pi = sub.add_parser("post-info", help="Get details on a specific post", aliases=["pi"])
    p_pi.add_argument("-p", "--post", required=True, help="Post URL or shortcode")
    add_session(p_pi)

    # 5. FOLLOWERS
    p_fol = sub.add_parser("followers", help="Extract followers list", aliases=["fl"])
    p_fol.add_argument("-u", "--username", required=True, help="Instagram username")
    p_fol.add_argument("--total", type=int, default=None, help="Max followers to fetch")
    add_session(p_fol)

    # 6. FOLLOWING
    p_fing = sub.add_parser("following", help="Extract following list", aliases=["fg"])
    p_fing.add_argument("-u", "--username", required=True, help="Instagram username")
    p_fing.add_argument("--total", type=int, default=None, help="Max following to fetch")
    add_session(p_fing)

    # 7. MUTUAL
    p_mut = sub.add_parser("mutual", help="Find mutual followers between two users")
    p_mut.add_argument("-u", "--username", required=True, help="First username")
    p_mut.add_argument("-u2", "--username2", required=True, help="Second username")
    p_mut.add_argument("--max", type=int, default=5000, help="Max followers per user")
    add_session(p_mut)

    # 8. HASHTAG
    p_hash = sub.add_parser("hashtag", help="Extract posts from a hashtag", aliases=["ht"])
    p_hash.add_argument("-t", "--tag", required=True, help="Hashtag (with or without #)")
    p_hash.add_argument("--total", type=int, default=50, help="Max posts (default: 50)")
    add_session(p_hash)

    # 9. SIMILAR
    p_sim = sub.add_parser("similar", help="Find similar/related accounts", aliases=["sim"])
    p_sim.add_argument("-u", "--username", required=True, help="Instagram username")
    add_session(p_sim)

    # 10. HIGHLIGHTS
    p_hl = sub.add_parser("highlights", help="Extract story highlights", aliases=["hl"])
    p_hl.add_argument("-u", "--username", required=True, help="Instagram username")
    add_session(p_hl)

    # 11. TAGGED
    p_tag = sub.add_parser("tagged", help="Extract posts the user is tagged in", aliases=["tg"])
    p_tag.add_argument("-u", "--username", required=True, help="Instagram username")
    p_tag.add_argument("--total", type=int, default=50, help="Max posts (default: 50)")
    add_session(p_tag)

    # 12. COMMENTS
    p_com = sub.add_parser("comments", help="Extract comments from a post", aliases=["cm"])
    p_com.add_argument("-m", "--media-id", required=True, help="Media/post ID")
    p_com.add_argument("--total", type=int, default=100, help="Max comments (default: 100)")
    add_session(p_com)

    # 13. CHECK
    p_chk = sub.add_parser("check", help="Check if a username exists", aliases=["ck"])
    p_chk.add_argument("-u", "--username", required=True, help="Username to check")
    add_session(p_chk)

    # 14. BIO LINK
    p_bio = sub.add_parser("biolink", help="Analyze a bio link (WHOIS, DNS)", aliases=["bl"])
    p_bio.add_argument("--url", required=True, help="URL to analyze")
    add_session(p_bio)

    # 15. RATIO
    p_rat = sub.add_parser("ratio", help="Analyze follower/following ratio", aliases=["r"])
    p_rat.add_argument("-u", "--username", required=True, help="Instagram username")
    add_session(p_rat)

    # 16. FULL SCAN
    p_full = sub.add_parser("fullscan", help="Run ALL intelligence modules on a user", aliases=["fs"])
    p_full.add_argument("-u", "--username", required=True, help="Instagram username")
    p_full.add_argument("--post-limit", type=int, default=10, help="Max posts (default: 10)")
    add_session(p_full)

    return parser


def build_api(args):
    """Construct InstaAPI from parsed CLI args."""
    proxy = None
    if hasattr(args, "proxy") and args.proxy:
        proxy = {"http": args.proxy, "https": args.proxy}
    sessions = getattr(args, "sessions", None)
    sid = getattr(args, "session_id", None)
    return InstaAPI(session_id=sid, session_ids=sessions or [], proxy=proxy)


def maybe_export(args, data, label):
    """Export data if --export flag was set."""
    fmt = getattr(args, "export", None)
    if fmt and data:
        from .modules.export import export_data
        username = getattr(args, "username", "data")
        export_data(data, f"{username}_{label}", fmt=fmt, label=label)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    print(BANNER)
    api = build_api(args)
    cmd = args.command

    # ─── PROFILE ───
    if cmd in ("profile", "p"):
        from .modules.profile import extract_profile, display_profile
        from .modules.lookup import advanced_email_phone_lookup, display_lookup, resolve_phone_country, display_phone_info
        data = extract_profile(api, args.username)
        if data:
            display_profile(data)
            # Also run advanced lookup for obfuscated email/phone
            lookup = advanced_email_phone_lookup(api, args.username)
            if lookup:
                display_lookup(lookup)
                if data:
                    data["obfuscated_email"] = lookup.get("obfuscated_email")
                    data["obfuscated_phone"] = lookup.get("obfuscated_phone")
                    data["can_email_reset"] = lookup.get("can_email_reset")
                    data["can_sms_reset"] = lookup.get("can_sms_reset")
            # Phone country resolution
            if data.get("public_phone_number") and data.get("public_phone_country_code"):
                phone_info = resolve_phone_country(data["public_phone_number"], data["public_phone_country_code"])
                display_phone_info(phone_info)
            maybe_export(args, data, "profile")

    # ─── LOOKUP ───
    elif cmd in ("lookup", "l"):
        from .modules.lookup import advanced_email_phone_lookup, display_lookup
        data = advanced_email_phone_lookup(api, args.username)
        display_lookup(data)
        maybe_export(args, data, "lookup")

    # ─── POSTS ───
    elif cmd in ("posts", "m"):
        from .modules.media import extract_user_posts, display_posts
        data = extract_user_posts(api, args.username, total=args.total, from_date=args.from_date, to_date=args.to_date)
        display_posts(data, show_urls=args.show_urls)
        maybe_export(args, data, "posts")

    # ─── POST INFO ───
    elif cmd in ("post-info", "pi"):
        from .modules.media import get_post_info, display_posts
        data = get_post_info(api, args.post)
        if data:
            display_posts([data], show_urls=True)
        maybe_export(args, data, "post_info")

    # ─── FOLLOWERS ───
    elif cmd in ("followers", "fl"):
        from .modules.social import extract_followers, display_followers
        data = extract_followers(api, args.username, total=args.total)
        display_followers(data, "FOLLOWERS")
        maybe_export(args, data, "followers")

    # ─── FOLLOWING ───
    elif cmd in ("following", "fg"):
        from .modules.social import extract_following, display_followers
        data = extract_following(api, args.username, total=args.total)
        display_followers(data, "FOLLOWING")
        maybe_export(args, data, "following")

    # ─── MUTUAL ───
    elif cmd == "mutual":
        from .modules.social import find_mutual_followers, display_mutual_followers
        data = find_mutual_followers(api, args.username, args.username2, max_per_user=args.max)
        display_mutual_followers(data, args.username, args.username2)
        maybe_export(args, data, "mutual")

    # ─── HASHTAG ───
    elif cmd in ("hashtag", "ht"):
        from .modules.hashtag import extract_hashtag_posts, display_hashtag_results
        data = extract_hashtag_posts(api, args.tag, total=args.total)
        display_hashtag_results(data, args.tag)
        maybe_export(args, data, "hashtag")

    # ─── SIMILAR ───
    elif cmd in ("similar", "sim"):
        from .modules.social import extract_similar_accounts, display_similar_accounts
        data = extract_similar_accounts(api, args.username)
        display_similar_accounts(data)
        maybe_export(args, data, "similar")

    # ─── HIGHLIGHTS ───
    elif cmd in ("highlights", "hl"):
        from .modules.media import extract_highlights, display_highlights
        data = extract_highlights(api, args.username)
        display_highlights(data)
        maybe_export(args, data, "highlights")

    # ─── TAGGED ───
    elif cmd in ("tagged", "tg"):
        from .modules.media import extract_tagged_posts, display_posts
        data = extract_tagged_posts(api, args.username, total=args.total)
        display_posts(data, show_urls=True)
        maybe_export(args, data, "tagged")

    # ─── COMMENTS ───
    elif cmd in ("comments", "cm"):
        from .modules.media import extract_comments, display_comments
        data = extract_comments(api, args.media_id, total=args.total)
        display_comments(data)
        maybe_export(args, data, "comments")

    # ─── CHECK ───
    elif cmd in ("check", "ck"):
        from .modules.profile import check_username_availability
        check_username_availability(api, args.username)

    # ─── BIO LINK ───
    elif cmd in ("biolink", "bl"):
        from .modules.lookup import bio_link_analysis, display_bio_link
        data = bio_link_analysis(args.url)
        display_bio_link(data)
        maybe_export(args, data, "biolink")

    # ─── RATIO ───
    elif cmd in ("ratio", "r"):
        from .modules.social import analyze_follower_following_ratio, display_ratio_analysis
        data = analyze_follower_following_ratio(api, args.username)
        display_ratio_analysis(data)

    # ─── FULL SCAN ───
    elif cmd in ("fullscan", "fs"):
        _run_full_scan(api, args)

    print()
    print_status("Done. Stay ethical. 🔒", "success")


def _run_full_scan(api, args):
    """Run all intelligence modules on a single username."""
    username = args.username
    from .modules.profile import extract_profile, display_profile
    from .modules.lookup import advanced_email_phone_lookup, display_lookup, resolve_phone_country, display_phone_info, bio_link_analysis, display_bio_link
    from .modules.media import extract_user_posts, display_posts, extract_highlights, display_highlights
    from .modules.social import extract_similar_accounts, display_similar_accounts, analyze_follower_following_ratio, display_ratio_analysis

    print_status(f"Starting FULL SCAN on @{username}...", "warning")
    print_separator("═")

    all_data = {}

    # Profile
    profile = extract_profile(api, username)
    if profile:
        display_profile(profile)
        all_data["profile"] = profile

    # Advanced Lookup
    lookup = advanced_email_phone_lookup(api, username)
    if lookup:
        display_lookup(lookup)
        all_data["lookup"] = lookup

    # Phone resolution
    if profile and profile.get("public_phone_number"):
        phone_info = resolve_phone_country(profile["public_phone_number"], profile.get("public_phone_country_code"))
        display_phone_info(phone_info)
        all_data["phone_info"] = phone_info

    # Bio link analysis
    ext_url = profile.get("external_url") if profile else None
    if ext_url:
        bio = bio_link_analysis(ext_url)
        display_bio_link(bio)
        all_data["bio_link"] = bio

    # Ratio analysis
    ratio = analyze_follower_following_ratio(api, username)
    display_ratio_analysis(ratio)
    all_data["ratio"] = ratio

    # Recent posts
    posts = extract_user_posts(api, username, total=args.post_limit)
    display_posts(posts)
    all_data["posts"] = posts

    # Highlights
    highlights = extract_highlights(api, username)
    display_highlights(highlights)
    all_data["highlights"] = highlights

    # Similar accounts
    similar = extract_similar_accounts(api, username)
    display_similar_accounts(similar)
    all_data["similar_accounts"] = similar

    maybe_export(args, all_data, "fullscan")
