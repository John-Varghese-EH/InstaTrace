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

    # Step 1: Web profile (primary public data)
    profile = {}
    user_id = None
    web_data = api.get_web_profile(username)
    
    if web_data and "data" in web_data and web_data["data"].get("user"):
        user = web_data["data"]["user"]
        user_id = user.get("id")
        profile.update({
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
        })
    else:
        # Step 1 fallback: Try to find user via search and scraping if main API is blocked
        error = web_data.get("error", "unknown") if (web_data and isinstance(web_data, dict)) else "no response"
        print_status(f"Primary API blocked ({error}) — attempting fallbacks...", "warning")
        
        # Fallback A: Search API
        search_data = api.get_user_by_search(username)
        if search_data and isinstance(search_data, dict):
            user_id = search_data.get("pk") or search_data.get("id")
            if user_id:
                print_status(f"Recovered user ID via search: {user_id}", "success")
                profile.update({
                    "user_id": user_id,
                    "username": search_data.get("username", username),
                    "full_name": search_data.get("full_name"),
                    "is_private": search_data.get("is_private"),
                    "is_verified": search_data.get("is_verified"),
                    "profile_pic_url": search_data.get("profile_pic_url"),
                })

        # Fallback B: HTML Scraping (extracts meta tags — very reliable)
        if not user_id:
            print_status("Scraping public profile page...", "info")
            scraped = api.scrape_profile_page(username)
            if scraped and isinstance(scraped, dict) and scraped.get("page_loaded"):
                # Try to get user ID from page metadata
                recovered_id = scraped.get("recovered_user_id")
                if recovered_id:
                    user_id = recovered_id
                    print_status(f"Recovered user ID from HTML: {user_id}", "success")

                # Extract user data from embedded JSON if available
                user_data = scraped.get("user_data")
                if user_data and isinstance(user_data, dict):
                    profile.update({
                        "user_id": user_data.get("id") or user_id,
                        "username": user_data.get("username", username),
                        "full_name": user_data.get("full_name"),
                        "biography": user_data.get("biography"),
                        "is_private": user_data.get("is_private"),
                        "follower_count": user_data.get("edge_followed_by", {}).get("count", 0),
                        "following_count": user_data.get("edge_follow", {}).get("count", 0),
                    })
                else:
                    # Use meta tag data as final fallback
                    print_status("Extracting from page meta tags...", "info")
                    profile["username"] = profile.get("username") or scraped.get("username", username)
                    profile["full_name"] = profile.get("full_name") or scraped.get("full_name")
                    profile["is_private"] = scraped.get("is_private")
                    profile["profile_pic_url"] = profile.get("profile_pic_url") or scraped.get("profile_pic_url")

                    # Parse raw counts from meta description
                    for key, raw_key in [("follower_count", "follower_count_raw"),
                                         ("following_count", "following_count_raw"),
                                         ("media_count", "post_count_raw")]:
                        raw = scraped.get(raw_key)
                        if raw and not profile.get(key):
                            profile[key] = _parse_count(raw)

                    if profile.get("full_name") or profile.get("follower_count"):
                        print_status("Recovered basic profile from HTML page", "success")
            elif scraped and scraped.get("error") == "not_found":
                print_status(f"@{username} does not exist (404)", "error")
                return None

    # If we still have no user_id but DO have scraped data, proceed anyway
    if not user_id and not profile.get("full_name") and not profile.get("follower_count"):
        print_status(f"Could not retrieve data for @{username}", "error")
        print_status("Tip: Use a session ID (-s) for most reliable access", "dim")
        return None

    # Set defaults
    profile.setdefault("username", username)
    profile.setdefault("user_id", user_id)

    # Step 2: Private API info (requires session — works on BOTH public and private)
    if user_id and api.has_session:
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
                "direct_messaging": priv.get("direct_messaging"),
                "fb_page_call_to_action_id": priv.get("fb_page_call_to_action_id"),
                "is_memorialized": priv.get("is_memorialized"),
                "is_new_to_instagram": priv.get("is_new_to_instagram"),
                "has_anonymous_profile_picture": priv.get("has_anonymous_profile_picture"),
                "account_type": priv.get("account_type"),
                "is_eligible_for_meta_verified": priv.get("is_eligible_for_meta_verified"),
                "is_meta_verified": priv.get("is_verified_by_mv4b"),
                "transparency_product_enabled": priv.get("transparency_product_enabled"),
                "has_biography_translation": priv.get("has_biography_translation"),
                "bio_entities": priv.get("biography_with_entities"),
                "total_igtv_videos": priv.get("total_igtv_videos"),
                "total_clips_count": priv.get("total_clips_count"),
                "total_ar_effects": priv.get("total_ar_effects"),
                "mutual_followers_count": priv.get("mutual_followers_count"),
                "hd_profile_pic_url": priv.get("hd_profile_pic_url_info", {}).get("url"),
                "profile_pic_id": priv.get("profile_pic_id"),
                "is_interest_account": priv.get("is_interest_account"),
                "has_chaining": priv.get("has_chaining"),
                "is_favorite": priv.get("is_favorite"),
                "is_favorite_for_stories": priv.get("is_favorite_for_stories"),
                "is_favorite_for_highlights": priv.get("is_favorite_for_highlights"),
                "live_subscription_status": priv.get("live_subscription_status"),
                "is_supervised_user": priv.get("is_supervised_user"),
                "is_guardian_of_viewer": priv.get("is_guardian_of_viewer"),
                "guardian_id": priv.get("guardian_id"),
                "is_eligible_for_shopping": priv.get("is_eligible_for_shopping"),
                "is_shopping_seller": priv.get("is_shopping_seller"),
                "fan_club_info": priv.get("fan_club_info"),
                "has_reels": priv.get("has_reels"),
                "latest_reel_media": priv.get("latest_reel_media"),
                "has_highlight_reels": priv.get("has_highlight_reels"),
                "is_bestie": priv.get("is_bestie"),
                "is_threads_user": priv.get("is_threads_user"),
                "interop_messaging_user_fbid": priv.get("interop_messaging_user_fbid"),
                "linked_fb_user": priv.get("linked_fb_user"),
                "fb_id_v2": priv.get("fbid_v2"),
                "page_id": priv.get("page_id"),
                "page_name": priv.get("page_name"),
            })

        # Full detail info (maximum data)
        print_status("Fetching full detail info (max data)...", "info")
        full_detail = api.get_user_full_detail(user_id)
        if full_detail and isinstance(full_detail, dict) and "user_detail" in full_detail:
            detail = full_detail.get("user_detail", {})
            user_detail = detail.get("user", {})
            for key, val in user_detail.items():
                if key not in profile or profile.get(key) is None:
                    profile[key] = val
            feed_items = detail.get("feed", {}).get("items", [])
            profile["recent_post_count_visible"] = len(feed_items)
            if feed_items:
                profile["last_post_timestamp"] = feed_items[0].get("taken_at")
                import datetime
                try:
                    profile["last_post_date"] = datetime.datetime.fromtimestamp(
                        feed_items[0]["taken_at"]).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass

        # Friendship status
        print_status("Checking friendship/relationship status...", "info")
        friendship = api.get_friendship_status(user_id)
        if friendship and isinstance(friendship, dict) and "error" not in friendship:
            profile["friendship"] = {
                "following": friendship.get("following"),
                "followed_by": friendship.get("followed_by"),
                "blocking": friendship.get("blocking"),
                "muting": friendship.get("muting"),
                "is_muting_reel": friendship.get("is_muting_reel"),
                "is_muting_notes": friendship.get("is_muting_notes"),
                "outgoing_request": friendship.get("outgoing_request"),
                "incoming_request": friendship.get("incoming_request"),
                "is_bestie": friendship.get("is_bestie"),
                "is_restricted": friendship.get("is_restricted"),
                "is_feed_favorite": friendship.get("is_feed_favorite"),
                "subscribed": friendship.get("subscribed"),
                "is_eligible_to_subscribe": friendship.get("is_eligible_to_subscribe"),
            }
            if profile.get("is_private"):
                if friendship.get("following"):
                    profile["_private_access"] = "ACCESSIBLE (you follow this private account)"
                else:
                    profile["_private_access"] = "LIMITED (private account — you don't follow them)"

        # Active stories
        print_status("Checking active stories...", "info")
        stories = api.get_user_stories(user_id)
        if stories and "reels" in stories:
            reels = stories.get("reels", {})
            reel = reels.get(str(user_id), {})
            story_items = reel.get("items", [])
            profile["active_stories_count"] = len(story_items)
            if story_items:
                profile["latest_story_timestamp"] = story_items[0].get("taken_at")

    elif user_id and not api.has_session:
        # ── SESSIONLESS / PUBLIC MODE ─────────────────────────────────
        print_status("Running in PUBLIC mode (no session ID provided)", "warning")
        print_status("Use -s <session_id> for full 60+ field extraction", "dim")

        # Search-based extraction (works without session)
        print_status("Extracting data via search API...", "info")
        search_data = api.get_user_by_search(username)
        if search_data and isinstance(search_data, dict):
            profile["full_name"] = profile.get("full_name") or search_data.get("full_name")
            profile["has_anonymous_profile_picture"] = search_data.get("has_anonymous_profile_picture")
            profile["latest_reel_media"] = search_data.get("latest_reel_media")

        # HTML page scraping (fallback — no session needed)
        print_status("Scraping public profile page for extra data...", "info")
        scraped = api.scrape_profile_page(username)
        if scraped and isinstance(scraped, dict):
            try:
                entry = scraped.get("entry_data", {}).get("ProfilePage", [{}])[0]
                graphql_user = entry.get("graphql", {}).get("user", {})
                if graphql_user:
                    profile["public_email"] = graphql_user.get("business_email")
                    profile["business_category"] = profile.get("business_category") or graphql_user.get("category_name")
            except:
                pass

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

    # Step 6: Advanced OSINT Analysis (Regex extraction & categorization)
    print_status("Running Advanced OSINT Analysis...", "info")
    profile["inferred_category"] = _categorize_account(profile)
    
    bio_text = profile.get("biography", "")
    profile["extracted_entities"] = _extract_entities_from_text(bio_text)
    profile["crypto_wallets"] = _extract_crypto_wallets(bio_text)
    
    # Also check external URL for PGP or Crypto
    external_url = profile.get("external_url", "")
    if external_url:
        crypto_links = _extract_crypto_wallets(external_url)
        for k, v in crypto_links.items():
            if isinstance(v, list):
                profile["crypto_wallets"].setdefault(k, []).extend(v)
            else:
                profile["crypto_wallets"][k] = v

    print_status("Profile extraction complete", "success")
    return profile


def _parse_count(raw):
    """Parse a raw count string like '1,234', '10.5K', '2.3M', '1B' into an integer."""
    if not raw:
        return 0
    raw = raw.strip().replace(",", "")
    try:
        # Handle K/M/B suffixes
        if raw.upper().endswith("B"):
            return int(float(raw[:-1]) * 1_000_000_000)
        elif raw.upper().endswith("M"):
            return int(float(raw[:-1]) * 1_000_000)
        elif raw.upper().endswith("K"):
            return int(float(raw[:-1]) * 1_000)
        return int(float(raw))
    except (ValueError, TypeError):
        return 0


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


def _extract_entities_from_text(text):
    """Extract emails, phone numbers, and URLs from plain text using Regex."""
    if not text:
        return {}
    import re
    entities = {}
    
    # Emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        entities['emails'] = list(set(emails))
        
    # Phone Numbers (International formats)
    phones = re.findall(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phones:
        entities['phones'] = list(set(phones))
        
    return entities


def _extract_crypto_wallets(text):
    """Extract cryptocurrency addresses (BTC, ETH, etc.) and PGP links."""
    if not text:
        return {}
    import re
    crypto = {}
    
    # Bitcoin (P2PKH, P2SH, Bech32)
    btc = re.findall(r'\b(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{39,59})\b', text)
    if btc: crypto['bitcoin'] = list(set(btc))
        
    # Ethereum (ERC-20 / ETH wallets)
    eth = re.findall(r'\b(0x[a-fA-F0-9]{40})\b', text)
    if eth: crypto['ethereum'] = list(set(eth))
        
    # PGP references
    if 'pgp' in text.lower() or 'keybase.io' in text.lower():
        crypto['pgp_mentioned'] = True
        
    return crypto


def _categorize_account(profile_data):
    """Heuristic categorization of the account based on stats and flags."""
    followers = profile_data.get('follower_count', 0)
    following = profile_data.get('following_count', 0)
    media = profile_data.get('media_count', 0)
    
    if profile_data.get('is_business') or profile_data.get('is_professional_account'):
        return "Business / Brand"
        
    if profile_data.get('is_verified'):
        return "Verified Celeb / Influencer"
        
    if followers > 50000:
        return "Influencer / Creator"
        
    # Bot / Fake detection heuristics
    if following > 2000 and followers < 100 and media < 5:
        return "High Probability Bot / Mass Follower"
        
    if followers == 0 and media == 0 and following > 50:
        return "Likely Bot / Lurker"
        
    return "Personal / Standard"


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
    print_field("Last Post Date", profile.get("last_post_date"))
    print_field("Active Stories", profile.get("active_stories_count"))
    
    # NEW OSINT Extractions Display
    print_section("ADVANCED OSINT ANALYSIS")
    
    category = profile.get("inferred_category")
    if category:
        color = C.ERROR if "Bot" in category else C.SUCCESS if "Influencer" in category else C.VALUE
        print_field("Inferred Category", f"{color}{category}{C.RESET}")
        
    entities = profile.get("extracted_entities", {})
    if entities:
        if entities.get("emails"):
            print_field("Bio Emails", ", ".join(entities["emails"]))
        if entities.get("phones"):
            print_field("Bio Phones", ", ".join(entities["phones"]))
            
    crypto = profile.get("crypto_wallets", {})
    if crypto:
        if crypto.get("bitcoin"):
            print_field("BTC Wallets", f"{C.WARNING}" + ", ".join(crypto["bitcoin"]) + f"{C.RESET}")
        if crypto.get("ethereum"):
            print_field("ETH Wallets", f"{C.LINK}" + ", ".join(crypto["ethereum"]) + f"{C.RESET}")
        if crypto.get("pgp_mentioned"):
            print_field("PGP Keys", f"{C.SUCCESS}Found PGP references in bio/links{C.RESET}")
    print_field("Running Ads", bool_icon(profile.get("is_running_ads")) if profile.get("is_running_ads") is not None else None)
    print_field("Memorial Account", bool_icon(profile.get("is_memorialized")) if profile.get("is_memorialized") is not None else None)
    print_field("New to Instagram", bool_icon(profile.get("is_new_to_instagram")) if profile.get("is_new_to_instagram") is not None else None)
    print_field("Joined Recently", bool_icon(profile.get("is_joined_recently")) if profile.get("is_joined_recently") is not None else None)
    print_field("Has Guides", bool_icon(profile.get("has_guides")) if profile.get("has_guides") is not None else None)
    print_field("Has Clips/Reels", bool_icon(profile.get("has_clips")) if profile.get("has_clips") is not None else None)
    print_field("Anonymous Profile Pic", bool_icon(profile.get("has_anonymous_profile_picture")) if profile.get("has_anonymous_profile_picture") is not None else None)
    print_field("Meta Verified Eligible", bool_icon(profile.get("is_eligible_for_meta_verified")) if profile.get("is_eligible_for_meta_verified") is not None else None)
    print_field("Meta Verified", bool_icon(profile.get("is_meta_verified")) if profile.get("is_meta_verified") is not None else None)
    print_field("Transparency Product", bool_icon(profile.get("transparency_product_enabled")) if profile.get("transparency_product_enabled") is not None else None)
    print_field("Supervised User", bool_icon(profile.get("is_supervised_user")) if profile.get("is_supervised_user") is not None else None)

    # Private Account Access
    if profile.get("is_private"):
        print_section("PRIVATE ACCOUNT STATUS")
        access = profile.get("_private_access", "NO SESSION — cannot determine access")
        color = C.SUCCESS if "ACCESSIBLE" in access else C.WARNING
        print(f"  {color}  {access}{C.RESET}")

    # Friendship / Relationship Status
    friendship = profile.get("friendship")
    if friendship:
        print_section("RELATIONSHIP STATUS")
        print_field("Following", bool_icon(friendship.get("following")))
        print_field("Followed By", bool_icon(friendship.get("followed_by")))
        print_field("Blocking", bool_icon(friendship.get("blocking")))
        print_field("Muting", bool_icon(friendship.get("muting")))
        print_field("Muting Reels", bool_icon(friendship.get("is_muting_reel")))
        print_field("Muting Notes", bool_icon(friendship.get("is_muting_notes")))
        print_field("Outgoing Request", bool_icon(friendship.get("outgoing_request")))
        print_field("Incoming Request", bool_icon(friendship.get("incoming_request")))
        print_field("Close Friend", bool_icon(friendship.get("is_bestie")))
        print_field("Restricted", bool_icon(friendship.get("is_restricted")))
        print_field("Feed Favorite", bool_icon(friendship.get("is_feed_favorite")))
        print_field("Subscribed", bool_icon(friendship.get("subscribed")))

    # Linked Accounts
    if profile.get("fb_id_v2") or profile.get("page_id") or profile.get("is_threads_user"):
        print_section("LINKED ACCOUNTS")
        print_field("Facebook ID", profile.get("fb_id_v2"))
        print_field("Facebook Page ID", profile.get("page_id"))
        print_field("Facebook Page Name", profile.get("page_name"))
        print_field("Threads User", bool_icon(profile.get("is_threads_user")) if profile.get("is_threads_user") is not None else None)
        print_field("Interop FB ID", profile.get("interop_messaging_user_fbid"))

    # Shopping & Monetization
    if any(profile.get(k) for k in ["is_eligible_for_shopping", "is_shopping_seller", "fan_club_info"]):
        print_section("SHOPPING & MONETIZATION")
        print_field("Shopping Eligible", bool_icon(profile.get("is_eligible_for_shopping")))
        print_field("Shopping Seller", bool_icon(profile.get("is_shopping_seller")))
        if profile.get("fan_club_info") and isinstance(profile["fan_club_info"], dict):
            print_field("Fan Club", profile["fan_club_info"].get("fan_club_name"))

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
