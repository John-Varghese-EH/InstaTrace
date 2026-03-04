"""
InstaTrace API Layer — Session management, request handling, multi-account rotation.
Author: John-Varghese-EH
"""

import requests
import json
import random
import time
import re
from urllib.parse import quote_plus
from json import dumps

from . import config


class InstaAPI:
    """Core Instagram private API interface with session rotation and rate limit handling."""

    def __init__(self, session_id=None, session_ids=None, proxy=None):
        """
        Initialize InstaAPI.

        Args:
            session_id:  Single Instagram session ID cookie.
            session_ids: List of session IDs for rotation (anti-rate-limit).
            proxy:       Proxy dict, e.g. {"http": "...", "https": "..."}.
        """
        self.session = requests.Session()
        self.proxy = proxy or config.PROXY
        self.session_id = session_id
        self.session_ids = session_ids or []
        self._session_pool = list(self.session_ids)
        self._request_count = 0
        self._rotate_after = random.randint(config.MIN_SESSION_REQUESTS, config.MAX_SESSION_REQUESTS)

        if self.proxy:
            self.session.proxies = self.proxy
            self.session.verify = False

        self._setup_session()

    def _setup_session(self):
        """Configure session headers and cookies."""
        self.session.headers.update({
            "User-Agent": config.random_ua(),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "X-IG-App-ID": config.IG_APP_ID,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": config.BASE_URL,
            "Connection": "keep-alive",
        })

        if self.session_id:
            self.session.cookies.set("sessionid", self.session_id, domain=".instagram.com")

    def _maybe_rotate_session(self):
        """Rotate to a different session ID to avoid rate limiting."""
        if not self.session_ids:
            return

        self._request_count += 1
        if self._request_count >= self._rotate_after:
            self._request_count = 0
            self._rotate_after = random.randint(config.MIN_SESSION_REQUESTS, config.MAX_SESSION_REQUESTS)

            if not self._session_pool:
                self._session_pool = list(self.session_ids)
            next_id = self._session_pool.pop(random.randint(0, len(self._session_pool) - 1))
            self.session.cookies.set("sessionid", next_id, domain=".instagram.com")
            self.session.headers["User-Agent"] = config.random_ua()

    def request(self, url, method="GET", params=None, data=None, headers=None, retries=None):
        """
        Make an API request with retry logic and rate limit handling.

        Returns:
            dict or None
        """
        retries = retries or config.MAX_RETRIES

        for attempt in range(1, retries + 1):
            try:
                self._maybe_rotate_session()

                resp = self.session.request(
                    method, url,
                    params=params, data=data, headers=headers,
                    timeout=config.REQUEST_TIMEOUT
                )

                if resp.status_code == 429:
                    wait = min(2 ** attempt, 30)
                    config.print_status(f"Rate limited — waiting {wait}s (attempt {attempt}/{retries})", "warning")
                    time.sleep(wait)
                    continue

                if resp.status_code == 404:
                    return {"error": "not_found", "status_code": 404}

                if resp.status_code == 401:
                    return {"error": "unauthorized", "status_code": 401}

                if "json" in resp.headers.get("Content-Type", ""):
                    return resp.json()

                return {"raw": resp.text, "status_code": resp.status_code}

            except requests.exceptions.Timeout:
                config.print_status(f"Timeout (attempt {attempt}/{retries})", "warning")
            except requests.exceptions.ConnectionError:
                config.print_status(f"Connection error (attempt {attempt}/{retries})", "error")
            except Exception as e:
                config.print_status(f"Request error: {e}", "error")
                return None

            time.sleep(1)

        config.print_status("All retries exhausted", "error")
        return None

    def graphql(self, query_hash, variables):
        """Execute a GraphQL query against Instagram."""
        params = {
            "query_hash": query_hash,
            "variables": json.dumps(variables)
        }
        return self.request(config.GRAPHQL_URL, params=params)

    # ─────────────── High-Level API Methods ───────────────

    def get_user_id(self, username):
        """Resolve a username to a numeric user ID."""
        url = config.USER_PROFILE_ENDPOINT.format(username)
        resp = self.request(url)
        if resp and "data" in resp:
            user = resp.get("data", {}).get("user")
            if user:
                return user.get("id")
        return None

    def get_user_info_by_id(self, user_id):
        """Get user info via the private API using a numeric user ID.
        Works on BOTH public and private accounts when authenticated."""
        url = config.USER_INFO_ENDPOINT.format(user_id)
        resp = self.request(url, headers={"User-Agent": "Instagram 64.0.0.14.96"})
        if resp and "user" in resp:
            return resp["user"]
        return resp

    def get_user_full_detail(self, user_id):
        """Get FULL user detail info — returns maximum data even for private accounts.
        This is the most data-rich endpoint. Requires session."""
        url = f"https://i.instagram.com/api/v1/users/{user_id}/full_detail_info/"
        resp = self.request(url, headers={"User-Agent": "Instagram 64.0.0.14.96"})
        return resp

    def get_web_profile(self, username):
        """Get user profile via the web profile endpoint."""
        url = config.USER_PROFILE_ENDPOINT.format(username)
        return self.request(url)

    def get_friendship_status(self, user_id):
        """Get friendship status (following, followed_by, blocking, muting, etc.).
        Reveals if the authenticated user follows the target (key for private access)."""
        url = f"https://i.instagram.com/api/v1/friendships/show/{user_id}/"
        return self.request(url, headers={"User-Agent": "Instagram 64.0.0.14.96"})

    def get_user_stories(self, user_id):
        """Get current active stories for a user. Works for private if you follow them."""
        url = config.STORY_ENDPOINT.format(user_id)
        return self.request(url, headers={"User-Agent": "Instagram 64.0.0.14.96"})

    def scrape_profile_page(self, username):
        """Scrape the public Instagram profile page HTML for embedded JSON data.
        Fallback method — can extract data even without API access."""
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": config.random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            resp = self.session.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return None
            # Try to extract shared_data JSON from page
            matches = re.findall(r'window\._sharedData\s*=\s*({.+?});', resp.text)
            if matches:
                return json.loads(matches[0])
            # Try script type="application/json" blocks
            json_blocks = re.findall(r'<script type="application/json"[^>]*>(.+?)</script>', resp.text)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if isinstance(data, dict):
                        return data
                except:
                    continue
            return {"raw_html_length": len(resp.text)}
        except Exception as e:
            return None

    def advanced_lookup(self, username):
        """
        Post to the recovery endpoint to get obfuscated login info
        (email/phone hints).
        """
        payload = "signed_body=SIGNATURE." + quote_plus(dumps(
            {"q": username, "skip_recovery": "1"},
            separators=(",", ":")
        ))
        headers = {
            "Accept-Language": "en-US",
            "User-Agent": "Instagram 101.0.0.15.120",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-App-ID": config.IG_APP_ID_ALT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "i.instagram.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(payload)),
        }
        return self.request(config.USER_LOOKUP_URL, method="POST", data=payload, headers=headers)

    def get_followers(self, user_id, max_id=None, count=100):
        """Get a page of followers for a user."""
        url = config.USER_FOLLOWERS_ENDPOINT.format(user_id)
        params = {"count": count}
        if max_id:
            params["max_id"] = max_id
        return self.request(url, params=params)

    def get_following(self, user_id, max_id=None, count=200):
        """Get a page of following for a user."""
        url = config.USER_FOLLOWINGS_ENDPOINT.format(user_id)
        params = {"count": count}
        if max_id:
            params["max_id"] = max_id
        return self.request(url, params=params)

    def get_user_feed(self, user_id, count=50, end_cursor=None):
        """Get user's timeline posts via GraphQL."""
        variables = {"id": user_id, "first": count}
        if end_cursor:
            variables["after"] = end_cursor
        return self.graphql(config.USER_FEED_QUERY, variables)

    def get_post_details(self, shortcode):
        """Get details of a specific post by its shortcode."""
        return self.graphql(config.POST_DETAILS_QUERY, {"shortcode": shortcode})

    def get_comments(self, media_id, max_id=None):
        """Get comments on a media item."""
        url = config.COMMENTS_ENDPOINT.format(media_id)
        params = {}
        if max_id:
            params["max_id"] = max_id
        return self.request(url, params=params)

    def get_highlights(self, user_id):
        """Get story highlight trays for a user."""
        url = config.HIGHLIGHTS_ENDPOINT.format(user_id)
        return self.request(url)

    def get_highlight_items(self, highlight_id):
        """Get items within a specific highlight reel."""
        url = config.STORY_HIGHLIGHTS_ENDPOINT.format(highlight_id)
        return self.request(url)

    def get_tagged_posts(self, user_id, max_id=None):
        """Get posts the user is tagged in."""
        url = config.TAGGED_ENDPOINT.format(user_id)
        params = {}
        if max_id:
            params["max_id"] = max_id
        return self.request(url, params=params)

    def get_similar_accounts(self, user_id):
        """Get Instagram's suggested similar accounts."""
        url = config.SIMILAR_ACCOUNTS_ENDPOINT.format(user_id)
        return self.request(url)

    def get_hashtag_posts(self, hashtag, count=50, end_cursor=None):
        """Get posts for a hashtag via GraphQL."""
        variables = {"tag_name": hashtag.lstrip("#"), "first": count}
        if end_cursor:
            variables["after"] = end_cursor
        return self.graphql(config.HASHTAG_QUERY, variables)

    def get_about_user(self, user_id):
        """Get about-this-account data (country, join date, ads, etc.)."""
        data = {
            "referer_type": "ProfileUsername",
            "target_user_id": user_id,
            "bk_client_context": json.dumps({
                "bloks_version": config.ABOUT_USER_QUERY,
                "style_id": "instagram"
            }),
            "bloks_versioning_id": config.ABOUT_USER_QUERY,
        }
        return self.request(config.ABOUT_USER_URL, method="POST", data=data)

    def search_users(self, query):
        """Search Instagram users by query."""
        url = config.USER_SEARCH_ENDPOINT.format(query)
        return self.request(url)

    def get_user_by_search(self, username):
        """Search for a user and return their data from search results.
        Alternative data source that works for private accounts."""
        resp = self.search_users(username)
        if resp and "users" in resp:
            for u in resp["users"]:
                if u.get("user", {}).get("username", "").lower() == username.lower():
                    return u.get("user")
        return None

    def check_username(self, username):
        """Check if a username exists by trying to fetch the profile page."""
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": config.random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            resp = self.session.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT, allow_redirects=False)
            return resp.status_code == 200
        except:
            return None
