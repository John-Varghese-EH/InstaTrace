"""
InstaTrace Hashtag Module — Hashtag intelligence and post extraction.
Author: John-Varghese-EH
"""

from ..config import C, print_status, print_field, print_section, print_separator
from .media import _parse_post_node


def extract_hashtag_posts(api, hashtag, total=50):
    """Extract posts from an Instagram hashtag."""
    tag = hashtag.lstrip("#")
    print_status(f"Extracting posts for #{tag}...", "info")
    posts, end_cursor, page = [], None, 0

    while len(posts) < total:
        page += 1
        resp = api.get_hashtag_posts(tag, end_cursor=end_cursor)
        if not resp:
            break
        try:
            media = resp["data"]["hashtag"]["edge_hashtag_to_media"]
        except (KeyError, TypeError):
            break
        edges = media.get("edges", [])
        if not edges:
            break
        for edge in edges:
            posts.append(_parse_post_node(edge.get("node", {})))
            if len(posts) >= total:
                break
        page_info = media.get("page_info", {})
        if not page_info.get("has_next_page"):
            break
        end_cursor = page_info.get("end_cursor")
        print_status(f"Page {page} — {len(posts)} posts...", "dim")

    print_status(f"Fetched {len(posts)} posts for #{tag}", "success")
    stats = {}
    if resp:
        try:
            td = resp.get("data", {}).get("hashtag", {})
            stats = {"name": td.get("name"), "post_count": td.get("edge_hashtag_to_media", {}).get("count")}
        except:
            pass
    return {"posts": posts, "stats": stats}


def display_hashtag_results(data, hashtag):
    """Display hashtag results."""
    stats, posts = data.get("stats", {}), data.get("posts", [])
    print_section(f"HASHTAG: #{hashtag.lstrip('#')}")
    if stats.get("post_count"):
        print_field("Total Posts", f"{stats['post_count']:,}")
    print_separator()
    for i, p in enumerate(posts[:25], 1):
        print(f"  {C.ACCENT}{i:3}. {C.DIM}[{p.get('type','')}] {C.VALUE}{p.get('datetime','')}{C.RESET}")
        print(f"       {C.DIM}♥ {p.get('likes',0):,} · 💬 {p.get('comments_count',0):,}{C.RESET}")
        cap = p.get("caption", "")[:80]
        if cap:
            print(f"       {C.VALUE}{cap}{C.RESET}")
    if len(posts) > 25:
        print(f"  {C.DIM}... and {len(posts)-25} more{C.RESET}")
    print()
    print_separator("═")
