"""
InstaTrace Profile Module — Full profile intelligence extraction.
Author: John-Varghese-EH
"""

import math
from ..config import C, print_status, print_field, print_section, print_separator, bool_icon


def extract_profile(api, username):
    """
    Extract comprehensive profile intelligence for a given username.

    Returns:
        dict: Full profile data, or None on error.
    """
    print_status(f"Fetching profile data for @{username}...", "info")

    # Step 1: Web profile (public data)
    web_data = api.get_web_profile(username)
    if not web_data or "error" in web_data:
        error = web_data.get("error", "unknown") if web_data else "no response"
        print_status(f"Failed to fetch profile: {error}", "error")
        return None

    user = web_data.get("data", {}).get("user")
    if not user:
        print_status("User not found", "error")
        return None

    user_id = user.get("id")
    profile = {
        "user_id": user_id,
        "username": user.get("username"),
        "full_name": user.get("full_name"),
        "biography": user.get("biography"),
        "bio_links": [link.get("url") for link in user.get("bio_links", [])],
        "external_url": user.get("external_url"),
        "profile_pic_url": user.get("profile_pic_url_hd"),
        "is_private": user.get("is_private"),
        "is_verified": user.get("is_verified"),
        "is_business": user.get("is_business_account"),
        "business_category": user.get("category_name"),
        "follower_count": user.get("edge_followed_by", {}).get("count", 0),
        "following_count": user.get("edge_follow", {}).get("count", 0),
        "media_count": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
        "is_joined_recently": user.get("is_joined_recently"),
        "has_channel": user.get("has_channel"),
        "has_guides": user.get("has_guides"),
        "highlight_reel_count": user.get("highlight_reel_count"),
        "has_clips": user.get("has_clips"),
        "pronouns": user.get("pronouns", []),
        "is_professional": user.get("is_professional_account"),
        "category_enum": user.get("category_enum"),
    }

    # Step 2: Private API info (if session is available)
    if user_id:
        print_status("Fetching extended info via private API...", "info")
        priv = api.get_user_info_by_id(user_id)
        if priv and isinstance(priv, dict) and "error" not in priv:
            profile.update({
                "public_email": priv.get("public_email"),
                "public_phone_number": priv.get("public_phone_number"),
                "public_phone_country_code": priv.get("public_phone_country_code"),
                "whatsapp_number": priv.get("whatsapp_number"),
                "is_whatsapp_linked": priv.get("is_whatsapp_linked"),
                "city_name": priv.get("city_name"),
                "address_street": priv.get("address_street"),
                "zip": priv.get("zip"),
                "contact_phone_number": priv.get("contact_phone_number"),
                "is_memorialized": priv.get("is_memorialized"),
                "is_new_to_instagram": priv.get("is_new_to_instagram"),
                "total_igtv_videos": priv.get("total_igtv_videos"),
                "total_clips_count": priv.get("total_clips_count"),
                "total_ar_effects": priv.get("total_ar_effects"),
                "hd_profile_pic_url": priv.get("hd_profile_pic_url_info", {}).get("url"),
                "has_anonymous_profile_picture": priv.get("has_anonymous_profile_picture"),
                "account_type": priv.get("account_type"),
                "is_eligible_for_meta_verified": priv.get("is_eligible_for_meta_verified"),
                "transparency_product_enabled": priv.get("transparency_product_enabled"),
                "mutual_followers_count": priv.get("mutual_followers_count"),
                "has_biography_translation": priv.get("has_biography_translation"),
                "bio_entities": priv.get("biography_with_entities"),
            })

    # Step 3: Estimate account age from user ID
    profile["estimated_account_age"] = _estimate_account_age(user_id)

    # Step 4: Calculate engagement rate from recent posts
    profile["engagement_rate"] = _calculate_engagement(web_data, profile["follower_count"])

    # Step 5: About This Account (previous usernames, creation date, country, ads)
    if user_id:
        print_status("Fetching About This Account data...", "info")
        about = api.get_about_user(user_id)
        about_parsed = _parse_about_data(about)
        if about_parsed:
            profile["date_joined"] = about_parsed.get("date_joined")
            profile["former_usernames"] = about_parsed.get("former_usernames", [])
            profile["username_changes_count"] = len(about_parsed.get("former_usernames", []))
            profile["account_country"] = about_parsed.get("country")
            profile["is_running_ads"] = about_parsed.get("is_running_ads")
            profile["date_verified"] = about_parsed.get("date_verified")
            profile["about_raw"] = about_parsed

    print_status("Profile extraction complete", "success")
    return profile


def _estimate_account_age(user_id):
    """
    Estimate approximate account creation year based on user ID ranges.
    These are rough approximations based on known ID ranges.
    """
    if not user_id:
        return "Unknown"
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return "Unknown"

    # Known approximate ID ranges by year
    ranges = [
        (50_000_000_000, "2022-2025 (Very New)"),
        (40_000_000_000, "2020-2022"),
        (20_000_000_000, "2019-2020"),
        (10_000_000_000, "2018-2019"),
        (5_000_000_000,  "2017-2018"),
        (2_000_000_000,  "2016-2017"),
        (1_000_000_000,  "2015-2016"),
        (500_000_000,    "2014-2015"),
        (100_000_000,    "2013-2014"),
        (10_000_000,     "2012-2013"),
        (1_000_000,      "2011-2012"),
        (0,              "2010-2011 (OG Account)"),
    ]

    for threshold, label in ranges:
        if uid >= threshold:
            return label
    return "Unknown"


def _calculate_engagement(web_data, follower_count):
    """Calculate engagement rate from recent visible posts."""
    try:
        user = web_data.get("data", {}).get("user", {})
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        if not edges or follower_count == 0:
            return None

        total_engagement = 0
        post_count = 0
        for edge in edges[:12]:
            node = edge.get("node", {})
            likes = node.get("edge_liked_by", {}).get("count", 0)
            comments = node.get("edge_media_to_comment", {}).get("count", 0)
            total_engagement += likes + comments
            post_count += 1

        if post_count == 0:
            return None

        avg_engagement = total_engagement / post_count
        rate = (avg_engagement / follower_count) * 100
        return round(rate, 2)
    except:
        return None


def _parse_about_data(response):
    """Parse the About This Account bloks response into structured data."""
    if not response or not isinstance(response, dict):
        return None

    result = {
        "date_joined": None,
        "former_usernames": [],
        "country": None,
        "is_running_ads": None,
        "date_verified": None,
    }

    # The about endpoint returns bloks data — extract text fields recursively
    _extract_about_fields(response, result)
    return result


def _extract_about_fields(data, result):
    """Recursively extract key fields from the bloks about-user response."""
    if isinstance(data, str):
        # Check for known field patterns in raw text
        lower = data.lower()
        if "date joined" in lower or "date_joined" in lower:
            result["_next_is_join_date"] = True
        elif "former usernames" in lower or "former_usernames" in lower:
            result["_next_is_usernames"] = True
        elif "country" in lower or "location" in lower:
            result["_next_is_country"] = True
        elif result.get("_next_is_join_date"):
            result["date_joined"] = data
            del result["_next_is_join_date"]
        elif result.get("_next_is_country"):
            result["country"] = data
            del result["_next_is_country"]
        return

    if isinstance(data, dict):
        # Look for structured text/key-value pairs
        for key, val in data.items():
            if key == "text" and isinstance(val, str):
                _extract_about_fields(val, result)
            elif key == "former_usernames" and isinstance(val, list):
                result["former_usernames"] = val
            elif key == "date_joined":
                result["date_joined"] = str(val)
            elif key == "account_country" or key.endswith("about_this_account_country"):
                if isinstance(val, str) and "bk.action.array.Make" in val:
                    result["country"] = val.split("bk.action.array.Make,")[-1].split(")")[0].replace('"', '').strip()
                else:
                    result["country"] = str(val)
            elif key == "is_active_ads_user":
                result["is_running_ads"] = bool(val)
            elif key == "date_verified":
                result["date_verified"] = str(val)
            else:
                _extract_about_fields(val, result)

    elif isinstance(data, list):
        # Check for former usernames patterns
        for item in data:
            _extract_about_fields(item, result)

        # Try to detect username lists (list of strings that look like usernames)
        if all(isinstance(x, str) and x.isascii() and len(x) < 50 for x in data if isinstance(x, str)):
            usernames = [x for x in data if isinstance(x, str) and not any(kw in x.lower() for kw in ["date", "country", "username", "account", "ads", "verified"])]
            if usernames and not result["former_usernames"]:
                # Don't override if already found
                pass


def display_profile(profile):
    """Display extracted profile data in a rich formatted output."""
    if not profile:
        return

    print_section("PROFILE INTELLIGENCE")
    print_field("Username", f"@{profile.get('username')}")
    print_field("User ID", profile.get("user_id"))
    print_field("Full Name", profile.get("full_name"))
    print_field("Account Type", _account_type_label(profile))
    print_field("Private Account", bool_icon(profile.get("is_private")))
    print_field("Verified", bool_icon(profile.get("is_verified")))
    print_field("Business Account", bool_icon(profile.get("is_business")))
    print_field("Business Category", profile.get("business_category"))
    print_field("Professional Account", bool_icon(profile.get("is_professional")))
    if profile.get("pronouns"):
        print_field("Pronouns", ", ".join(profile["pronouns"]))

    print_section("ACCOUNT STATS")
    print_field("Followers", f"{profile.get('follower_count', 0):,}")
    print_field("Following", f"{profile.get('following_count', 0):,}")
    print_field("Posts", f"{profile.get('media_count', 0):,}")
    print_field("IGTV Videos", profile.get("total_igtv_videos"))
    print_field("Reels/Clips", profile.get("total_clips_count"))
    print_field("AR Effects", profile.get("total_ar_effects"))
    print_field("Story Highlights", profile.get("highlight_reel_count"))
    if profile.get("engagement_rate") is not None:
        rate = profile["engagement_rate"]
        color = C.SUCCESS if rate > 3 else C.WARNING if rate > 1 else C.ERROR
        print_field("Engagement Rate", f"{color}{rate}%{C.RESET}")

    print_section("BIOGRAPHY")
    bio = profile.get("biography", "")
    if bio:
        for line in bio.split("\n"):
            print(f"  {C.VALUE}  {line}{C.RESET}")
    else:
        print(f"  {C.DIM}  (no bio){C.RESET}")

    if profile.get("external_url"):
        print()
        print_field("External URL", profile["external_url"])
    if profile.get("bio_links"):
        for i, link in enumerate(profile["bio_links"], 1):
            print_field(f"Bio Link #{i}", link)

    print_section("CONTACT INFO")
    print_field("Public Email", profile.get("public_email"))
    print_field("Public Phone", _format_phone(profile))
    print_field("WhatsApp Number", profile.get("whatsapp_number"))
    print_field("WhatsApp Linked", bool_icon(profile.get("is_whatsapp_linked")) if profile.get("is_whatsapp_linked") is not None else None)
    print_field("City", profile.get("city_name"))
    print_field("Street Address", profile.get("address_street"))
    print_field("ZIP Code", profile.get("zip"))
    print_field("Contact Phone", profile.get("contact_phone_number"))

    print_section("ACCOUNT METADATA")
    print_field("Date Joined", profile.get("date_joined"))
    print_field("Est. Account Age", profile.get("estimated_account_age"))
    print_field("Account Country", profile.get("account_country"))
    print_field("Date Verified", profile.get("date_verified"))
    print_field("Running Ads", bool_icon(profile.get("is_running_ads")) if profile.get("is_running_ads") is not None else None)
    print_field("Memorial Account", bool_icon(profile.get("is_memorialized")) if profile.get("is_memorialized") is not None else None)
    print_field("New to Instagram", bool_icon(profile.get("is_new_to_instagram")) if profile.get("is_new_to_instagram") is not None else None)
    print_field("Joined Recently", bool_icon(profile.get("is_joined_recently")) if profile.get("is_joined_recently") is not None else None)
    print_field("Has Guides", bool_icon(profile.get("has_guides")) if profile.get("has_guides") is not None else None)
    print_field("Has Clips/Reels", bool_icon(profile.get("has_clips")) if profile.get("has_clips") is not None else None)
    print_field("Anonymous Profile Pic", bool_icon(profile.get("has_anonymous_profile_picture")) if profile.get("has_anonymous_profile_picture") is not None else None)
    print_field("Meta Verified Eligible", bool_icon(profile.get("is_eligible_for_meta_verified")) if profile.get("is_eligible_for_meta_verified") is not None else None)
    print_field("Transparency Product", bool_icon(profile.get("transparency_product_enabled")) if profile.get("transparency_product_enabled") is not None else None)

    # Former Usernames
    former = profile.get("former_usernames", [])
    if former:
        print_section(f"FORMER USERNAMES ({len(former)} changes)")
        for i, name in enumerate(former, 1):
            print(f"  {C.DIM}{i:3}. {C.WARNING}@{name}{C.RESET}")
    else:
        print_section("FORMER USERNAMES")
        changes = profile.get("username_changes_count", 0)
        if changes:
            print_field("Username Changes", str(changes))
        else:
            print(f"  {C.DIM}  No former usernames found (or data not accessible){C.RESET}")

    print_section("PROFILE PICTURE")
    hd_url = profile.get("hd_profile_pic_url") or profile.get("profile_pic_url")
    if hd_url:
        print(f"  {C.LINK}  {hd_url}{C.RESET}")
    else:
        print(f"  {C.DIM}  (not available){C.RESET}")

    print()
    print_separator("═")


def _account_type_label(profile):
    """Return human-readable account type."""
    types = {1: "Personal", 2: "Business", 3: "Creator"}
    return types.get(profile.get("account_type"), "Unknown")


def _format_phone(profile):
    """Format phone number with country code."""
    phone = profile.get("public_phone_number")
    if not phone:
        return None
    cc = profile.get("public_phone_country_code")
    if cc:
        return f"+{cc} {phone}"
    return str(phone)


def check_username_availability(api, username):
    """Check if a username exists on Instagram."""
    print_status(f"Checking availability of @{username}...", "info")
    exists = api.check_username(username)
    if exists is True:
        print_status(f"@{username} EXISTS — account is active", "warning")
    elif exists is False:
        print_status(f"@{username} AVAILABLE — no account found", "success")
    else:
        print_status(f"Could not determine status for @{username}", "dim")
    return exists
