"""
InstaTrace Social Graph Module — Followers, following, mutual analysis, similar accounts.
Author: John-Varghese-EH
"""

from ..config import C, print_status, print_field, print_section, print_separator, bool_icon


def extract_followers(api, username, total=None):
    """
    Extract followers list for a user.

    Args:
        api:      InstaAPI instance.
        username: Instagram username.
        total:    Max followers to fetch. None = all.

    Returns:
        list: Follower user dicts.
    """
    user_id = api.get_user_id(username)
    if not user_id:
        print_status(f"Could not resolve user ID for @{username}", "error")
        return []

    print_status(f"Extracting followers for @{username} (ID: {user_id})...", "info")
    followers = []
    max_id = None
    page = 0

    while True:
        page += 1
        resp = api.get_followers(user_id, max_id=max_id)
        if not resp or "users" not in resp:
            break

        for u in resp["users"]:
            followers.append(_parse_user(u))
            if total and len(followers) >= total:
                print_status(f"Fetched {len(followers)} followers (limit reached)", "success")
                return followers

        max_id = resp.get("next_max_id")
        if not max_id:
            break

        print_status(f"Page {page} — {len(followers)} followers so far...", "dim")

    print_status(f"Fetched {len(followers)} total followers", "success")
    return followers


def extract_following(api, username, total=None):
    """
    Extract following list for a user.

    Args:
        api:      InstaAPI instance.
        username: Instagram username.
        total:    Max following to fetch. None = all.

    Returns:
        list: Following user dicts.
    """
    user_id = api.get_user_id(username)
    if not user_id:
        print_status(f"Could not resolve user ID for @{username}", "error")
        return []

    print_status(f"Extracting following for @{username} (ID: {user_id})...", "info")
    following = []
    max_id = None
    page = 0

    while True:
        page += 1
        resp = api.get_following(user_id, max_id=max_id)
        if not resp or "users" not in resp:
            break

        for u in resp["users"]:
            following.append(_parse_user(u))
            if total and len(following) >= total:
                print_status(f"Fetched {len(following)} following (limit reached)", "success")
                return following

        max_id = resp.get("next_max_id")
        if not max_id:
            break

        print_status(f"Page {page} — {len(following)} following so far...", "dim")

    print_status(f"Fetched {len(following)} total following", "success")
    return following


def find_mutual_followers(api, username1, username2, max_per_user=5000):
    """
    Find mutual followers between two accounts.

    Args:
        api:            InstaAPI instance.
        username1:      First username.
        username2:      Second username.
        max_per_user:   Max followers to fetch per user.

    Returns:
        dict: {mutual: list, counts, percentages}
    """
    print_section("MUTUAL FOLLOWER ANALYSIS")
    print_status(f"Comparing @{username1} and @{username2}...", "info")

    print_status(f"Fetching followers for @{username1}...", "info")
    followers1 = extract_followers(api, username1, total=max_per_user)
    set1 = {u["username"] for u in followers1}

    print_status(f"Fetching followers for @{username2}...", "info")
    followers2 = extract_followers(api, username2, total=max_per_user)
    set2 = {u["username"] for u in followers2}

    mutual = set1 & set2
    only_1 = set1 - set2
    only_2 = set2 - set1

    result = {
        "mutual": sorted(mutual),
        "mutual_count": len(mutual),
        "only_user1": len(only_1),
        "only_user2": len(only_2),
        "total_user1": len(set1),
        "total_user2": len(set2),
        "overlap_percent_1": round(len(mutual) / max(len(set1), 1) * 100, 1),
        "overlap_percent_2": round(len(mutual) / max(len(set2), 1) * 100, 1),
    }

    print_status(f"Found {len(mutual)} mutual followers", "success")
    return result


def extract_similar_accounts(api, username):
    """
    Get Instagram-suggested similar accounts.

    Returns:
        list: Similar account dicts.
    """
    user_id = api.get_user_id(username)
    if not user_id:
        print_status(f"Could not resolve user ID for @{username}", "error")
        return []

    print_status(f"Finding similar accounts to @{username}...", "info")
    resp = api.get_similar_accounts(user_id)

    if not resp or "users" not in resp:
        print_status("No similar accounts found", "warning")
        return []

    accounts = []
    for u in resp.get("users", []):
        accounts.append({
            "username": u.get("username"),
            "full_name": u.get("full_name"),
            "is_verified": u.get("is_verified"),
            "is_private": u.get("is_private"),
            "follower_count": u.get("follower_count"),
            "profile_pic_url": u.get("profile_pic_url"),
            "chaining_info": u.get("chaining_info"),
        })

    print_status(f"Found {len(accounts)} similar accounts", "success")
    return accounts


def analyze_follower_following_ratio(api, username):
    """
    Analyze the follower/following ratio and provide insights.

    Returns:
        dict: Analysis results.
    """
    web_data = api.get_web_profile(username)
    if not web_data:
        return None

    user = web_data.get("data", {}).get("user", {})
    followers = user.get("edge_followed_by", {}).get("count", 0)
    following = user.get("edge_follow", {}).get("count", 0)

    ratio = round(followers / max(following, 1), 2)

    if ratio > 10:
        verdict = "Influencer / Celebrity (high follower-to-following ratio)"
    elif ratio > 2:
        verdict = "Popular / Growing Account"
    elif ratio > 0.5:
        verdict = "Normal / Active User"
    elif ratio > 0.1:
        verdict = "Follow-Heavy (follows more than followed by)"
    else:
        verdict = "Possible Bot / Mass-Follower Pattern"

    return {
        "username": username,
        "followers": followers,
        "following": following,
        "ratio": ratio,
        "verdict": verdict,
    }


# ═══════════════════════ DISPLAY ═══════════════════════

def display_followers(users, title="FOLLOWERS"):
    """Display a list of users."""
    if not users:
        print_status("No users to display", "dim")
        return

    print_section(f"{title} ({len(users)} total)")

    for i, u in enumerate(users, 1):
        verified = f" {C.HEADER}✓{C.RESET}" if u.get("is_verified") else ""
        private = f" {C.DIM}🔒{C.RESET}" if u.get("is_private") else ""
        name = f" ({u.get('full_name')})" if u.get("full_name") else ""
        print(f"  {C.DIM}{i:5}. {C.VALUE}@{u.get('username', 'unknown')}{verified}{private}{C.DIM}{name}{C.RESET}")

    print()
    print_separator("═")


def display_mutual_followers(result, username1, username2):
    """Display mutual follower analysis."""
    print_section("MUTUAL FOLLOWER RESULTS")
    print_field(f"@{username1} followers fetched", f"{result['total_user1']:,}")
    print_field(f"@{username2} followers fetched", f"{result['total_user2']:,}")
    print_separator()
    print_field("Mutual Followers", f"{C.SUCCESS}{result['mutual_count']:,}{C.RESET}")
    print_field(f"Only @{username1}", f"{result['only_user1']:,}")
    print_field(f"Only @{username2}", f"{result['only_user2']:,}")
    print_field(f"Overlap % of @{username1}", f"{result['overlap_percent_1']}%")
    print_field(f"Overlap % of @{username2}", f"{result['overlap_percent_2']}%")

    if result["mutual"] and len(result["mutual"]) <= 100:
        print()
        print_status("Mutual followers:", "info")
        for i, u in enumerate(result["mutual"], 1):
            print(f"  {C.DIM}{i:5}. {C.VALUE}@{u}{C.RESET}")

    print()
    print_separator("═")


def display_similar_accounts(accounts):
    """Display similar accounts."""
    if not accounts:
        print_status("No similar accounts to display", "dim")
        return

    print_section(f"SIMILAR ACCOUNTS ({len(accounts)} total)")

    for i, a in enumerate(accounts, 1):
        verified = f" {C.HEADER}✓{C.RESET}" if a.get("is_verified") else ""
        followers = f" · {a.get('follower_count', 0):,} followers" if a.get("follower_count") else ""
        name = f" ({a.get('full_name')})" if a.get("full_name") else ""
        print(f"  {C.DIM}{i:3}. {C.VALUE}@{a.get('username', 'unknown')}{verified}{C.DIM}{name}{followers}{C.RESET}")

    print()
    print_separator("═")


def display_ratio_analysis(result):
    """Display follower/following ratio analysis."""
    if not result:
        return

    print_section("FOLLOWER/FOLLOWING RATIO ANALYSIS")
    print_field("Username", f"@{result['username']}")
    print_field("Followers", f"{result['followers']:,}")
    print_field("Following", f"{result['following']:,}")
    print_field("Ratio", f"{result['ratio']}")
    print_field("Assessment", result['verdict'])
    print()
    print_separator("═")


# ═══════════════════════ HELPERS ═══════════════════════

def _parse_user(u):
    """Parse a user dict from the API response."""
    return {
        "user_id": u.get("pk") or u.get("id"),
        "username": u.get("username"),
        "full_name": u.get("full_name"),
        "is_private": u.get("is_private"),
        "is_verified": u.get("is_verified"),
        "profile_pic_url": u.get("profile_pic_url"),
        "has_anonymous_profile_picture": u.get("has_anonymous_profile_picture"),
    }
