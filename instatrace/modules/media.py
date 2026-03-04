"""
InstaTrace Media Module — Post extraction, media URLs, comments, story highlights, tagged posts.
Author: John-Varghese-EH
"""

import datetime
from ..config import C, print_status, print_field, print_section, print_separator


def extract_user_posts(api, username, total=None, from_date=None, to_date=None):
    """
    Extract posts from a user's timeline with optional date filtering.

    Args:
        api:        InstaAPI instance.
        username:   Instagram username.
        total:      Max number of posts to fetch. None = all.
        from_date:  Fetch posts after this date (YYYY-MM-DD).
        to_date:    Fetch posts before this date (YYYY-MM-DD).

    Returns:
        list: Post data dicts.
    """
    user_id = api.get_user_id(username)
    if not user_id:
        print_status(f"Could not resolve user ID for @{username}", "error")
        return []

    print_status(f"Extracting posts for @{username} (ID: {user_id})...", "info")

    from_dt = _parse_date(from_date) if from_date else None
    to_dt = _parse_date(to_date) if to_date else None

    posts = []
    end_cursor = None
    page = 0

    while True:
        page += 1
        resp = api.get_user_feed(user_id, end_cursor=end_cursor)
        if not resp:
            break

        try:
            media = resp["data"]["user"]["edge_owner_to_timeline_media"]
        except (KeyError, TypeError):
            print_status("Could not parse media response", "warning")
            break

        edges = media.get("edges", [])
        if not edges:
            break

        for edge in edges:
            node = edge.get("node", {})
            post = _parse_post_node(node)

            # Date filtering
            if from_dt and post.get("timestamp"):
                post_dt = datetime.datetime.fromtimestamp(post["timestamp"])
                if post_dt < from_dt:
                    continue
            if to_dt and post.get("timestamp"):
                post_dt = datetime.datetime.fromtimestamp(post["timestamp"])
                if post_dt > to_dt:
                    print_status(f"Fetched {len(posts)} posts (reached date limit)", "success")
                    return posts

            posts.append(post)

            if total and len(posts) >= total:
                print_status(f"Fetched {len(posts)} posts (reached limit)", "success")
                return posts

        # Pagination
        page_info = media.get("page_info", {})
        if not page_info.get("has_next_page"):
            break
        end_cursor = page_info.get("end_cursor")
        print_status(f"Page {page} — {len(posts)} posts so far...", "dim")

    print_status(f"Fetched {len(posts)} total posts", "success")
    return posts


def get_post_info(api, post_url):
    """
    Get detailed information about a specific Instagram post.

    Args:
        api:      InstaAPI instance.
        post_url: Full Instagram post URL or shortcode.

    Returns:
        dict: Post details.
    """
    shortcode = _extract_shortcode(post_url)
    if not shortcode:
        print_status("Invalid post URL or shortcode", "error")
        return None

    print_status(f"Fetching post details for {shortcode}...", "info")
    resp = api.get_post_details(shortcode)

    if not resp or "data" not in resp:
        print_status("Could not fetch post details", "error")
        return None

    media = resp.get("data", {}).get("shortcode_media")
    if not media:
        print_status("Post not found", "error")
        return None

    post = {
        "shortcode": shortcode,
        "type": media.get("__typename"),
        "id": media.get("id"),
        "caption": _get_caption(media),
        "timestamp": media.get("taken_at_timestamp"),
        "datetime": _format_timestamp(media.get("taken_at_timestamp")),
        "likes": media.get("edge_media_preview_like", {}).get("count", 0),
        "comments_count": media.get("edge_media_to_parent_comment", {}).get("count", 0),
        "video_views": media.get("video_view_count"),
        "is_video": media.get("is_video"),
        "video_url": media.get("video_url"),
        "display_url": media.get("display_url"),
        "dimensions": media.get("dimensions"),
        "location": _extract_location(media),
        "owner": {
            "id": media.get("owner", {}).get("id"),
            "username": media.get("owner", {}).get("username"),
            "full_name": media.get("owner", {}).get("full_name"),
        },
        "is_ad": media.get("is_ad"),
        "accessibility_caption": media.get("accessibility_caption"),
        "media_urls": _extract_media_urls(media),
    }

    print_status("Post details extracted", "success")
    return post


def extract_comments(api, media_id, total=100):
    """
    Extract comments from a post.

    Args:
        api:      InstaAPI instance.
        media_id: Instagram media ID.
        total:    Maximum comments to fetch.

    Returns:
        list: Comment data dicts.
    """
    print_status(f"Extracting comments for media {media_id}...", "info")
    comments = []
    max_id = None

    while len(comments) < total:
        resp = api.get_comments(media_id, max_id=max_id)
        if not resp or "comments" not in resp:
            break

        for c in resp["comments"]:
            comments.append({
                "user": c.get("user", {}).get("username"),
                "user_id": c.get("user", {}).get("pk"),
                "text": c.get("text"),
                "timestamp": c.get("created_at"),
                "datetime": _format_timestamp(c.get("created_at")),
                "likes": c.get("comment_like_count", 0),
                "reply_count": c.get("child_comment_count", 0),
                "is_verified": c.get("user", {}).get("is_verified"),
            })
            if len(comments) >= total:
                break

        max_id = resp.get("next_min_id")
        if not max_id:
            break

    print_status(f"Extracted {len(comments)} comments", "success")
    return comments


def extract_highlights(api, username):
    """
    Extract story highlight trays for a user.

    Returns:
        list: Highlight data dicts.
    """
    user_id = api.get_user_id(username)
    if not user_id:
        print_status(f"Could not resolve user ID for @{username}", "error")
        return []

    print_status(f"Fetching story highlights for @{username}...", "info")
    resp = api.get_highlights(user_id)

    if not resp or "tray" not in resp:
        print_status("No highlights found or not accessible", "warning")
        return []

    highlights = []
    for item in resp.get("tray", []):
        highlights.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "media_count": item.get("media_count"),
            "cover_url": item.get("cover_media", {}).get("cropped_image_version", {}).get("url"),
            "created_at": _format_timestamp(item.get("created_at")),
        })

    print_status(f"Found {len(highlights)} story highlights", "success")
    return highlights


def extract_tagged_posts(api, username, total=50):
    """
    Extract posts the user is tagged in.

    Returns:
        list: Tagged post data dicts.
    """
    user_id = api.get_user_id(username)
    if not user_id:
        print_status(f"Could not resolve user ID for @{username}", "error")
        return []

    print_status(f"Fetching tagged posts for @{username}...", "info")
    posts = []
    max_id = None

    while len(posts) < total:
        resp = api.get_tagged_posts(user_id, max_id=max_id)
        if not resp or "items" not in resp:
            break

        for item in resp["items"]:
            posts.append(_parse_post_node(item, is_api=True))
            if len(posts) >= total:
                break

        max_id = resp.get("next_max_id")
        if not max_id:
            break

    print_status(f"Found {len(posts)} tagged posts", "success")
    return posts


def display_posts(posts, show_urls=False):
    """Display extracted posts in formatted output."""
    if not posts:
        print_status("No posts to display", "dim")
        return

    print_section(f"POSTS ({len(posts)} total)")

    for i, post in enumerate(posts, 1):
        print(f"\n  {C.ACCENT}  ┌─ Post #{i}{C.RESET}")
        print_field("Type", post.get("type", "Unknown"), label_width=20)
        print_field("Shortcode", post.get("shortcode"), label_width=20)
        print_field("Date", post.get("datetime"), label_width=20)
        print_field("Likes", f"{post.get('likes', 0):,}", label_width=20)
        print_field("Comments", f"{post.get('comments_count', 0):,}", label_width=20)
        if post.get("video_views"):
            print_field("Views", f"{post['video_views']:,}", label_width=20)
        if post.get("caption"):
            cap = post["caption"][:120] + ("..." if len(post["caption"]) > 120 else "")
            print_field("Caption", cap, label_width=20)
        if post.get("location", {}).get("name"):
            print_field("Location", post["location"]["name"], label_width=20)
        if show_urls and post.get("media_urls"):
            for j, url in enumerate(post["media_urls"], 1):
                print(f"  {C.DIM}│   Media {j}: {C.LINK}{url[:80]}...{C.RESET}")
        print(f"  {C.ACCENT}  └───────────{C.RESET}")

    print()
    print_separator("═")


def display_comments(comments):
    """Display extracted comments."""
    if not comments:
        print_status("No comments to display", "dim")
        return

    print_section(f"COMMENTS ({len(comments)} total)")

    for i, c in enumerate(comments, 1):
        verified = " ✓" if c.get("is_verified") else ""
        print(f"  {C.ACCENT}  {i:3}. {C.HEADER}@{c.get('user', 'unknown')}{verified}{C.RESET}")
        print(f"       {C.VALUE}{c.get('text', '')}{C.RESET}")
        print(f"       {C.DIM}{c.get('datetime', '')} · ♥ {c.get('likes', 0)} · {c.get('reply_count', 0)} replies{C.RESET}")

    print()
    print_separator("═")


def display_highlights(highlights):
    """Display story highlights."""
    if not highlights:
        print_status("No highlights to display", "dim")
        return

    print_section(f"STORY HIGHLIGHTS ({len(highlights)} total)")

    for i, h in enumerate(highlights, 1):
        print_field(f"  #{i} {h.get('title', 'Untitled')}", f"{h.get('media_count', 0)} items")

    print()
    print_separator("═")


# ═══════════════════════ HELPERS ═══════════════════════

def _parse_post_node(node, is_api=False):
    """Parse a post node from either GraphQL or API response."""
    if is_api:
        return {
            "id": node.get("pk") or node.get("id"),
            "shortcode": node.get("code"),
            "type": _media_type(node.get("media_type")),
            "timestamp": node.get("taken_at"),
            "datetime": _format_timestamp(node.get("taken_at")),
            "likes": node.get("like_count", 0),
            "comments_count": node.get("comment_count", 0),
            "caption": (node.get("caption", {}) or {}).get("text", ""),
            "location": {"name": (node.get("location") or {}).get("name")},
            "media_urls": [],
        }

    return {
        "id": node.get("id"),
        "shortcode": node.get("shortcode"),
        "type": node.get("__typename", "Unknown"),
        "timestamp": node.get("taken_at_timestamp"),
        "datetime": _format_timestamp(node.get("taken_at_timestamp")),
        "likes": node.get("edge_liked_by", {}).get("count", 0) or node.get("edge_media_preview_like", {}).get("count", 0),
        "comments_count": node.get("edge_media_to_comment", {}).get("count", 0),
        "caption": _get_caption(node),
        "location": _extract_location(node),
        "is_video": node.get("is_video"),
        "video_views": node.get("video_view_count"),
        "media_urls": [node.get("display_url")] if node.get("display_url") else [],
        "accessibility_caption": node.get("accessibility_caption"),
    }


def _extract_media_urls(media):
    """Extract all media URLs from a post."""
    urls = []
    typename = media.get("__typename")

    if typename == "GraphImage":
        resources = media.get("display_resources", [])
        if resources:
            urls.append(resources[-1].get("src"))
        elif media.get("display_url"):
            urls.append(media["display_url"])
    elif typename == "GraphVideo":
        if media.get("video_url"):
            urls.append(media["video_url"])
    elif typename == "GraphSidecar":
        for edge in media.get("edge_sidecar_to_children", {}).get("edges", []):
            node = edge.get("node", {})
            if node.get("is_video") and node.get("video_url"):
                urls.append(node["video_url"])
            else:
                resources = node.get("display_resources", [])
                if resources:
                    urls.append(resources[-1].get("src"))
                elif node.get("display_url"):
                    urls.append(node["display_url"])

    return urls


def _extract_location(media):
    """Extract location info from a media node."""
    loc = media.get("location")
    if not loc:
        return {}
    return {
        "id": loc.get("id"),
        "name": loc.get("name"),
        "slug": loc.get("slug"),
        "has_public_page": loc.get("has_public_page"),
        "address": loc.get("address_json"),
    }


def _get_caption(media):
    """Extract caption text from a media node."""
    edges = media.get("edge_media_to_caption", {}).get("edges", [])
    if edges:
        return edges[0].get("node", {}).get("text", "")
    return ""


def _extract_shortcode(url_or_code):
    """Extract shortcode from a URL or return as-is if already a code."""
    if "/" in url_or_code:
        parts = url_or_code.rstrip("/").split("/")
        # URL is like .../p/SHORTCODE/ or .../reel/SHORTCODE/
        for i, part in enumerate(parts):
            if part in ("p", "reel", "tv") and i + 1 < len(parts):
                return parts[i + 1]
        return parts[-1]
    return url_or_code


def _format_timestamp(ts):
    """Convert Unix timestamp to readable datetime string."""
    if not ts:
        return None
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)


def _media_type(code):
    """Convert API media type code to human-readable string."""
    types = {1: "Photo", 2: "Video", 8: "Carousel"}
    return types.get(code, "Unknown")


def _parse_date(date_str):
    """Parse a YYYY-MM-DD date string."""
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")
