<div align="center">

# 🔍 InstaTrace

### Ultimate Instagram OSINT Intelligence Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-red.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-instatrace-green.svg)](https://pypi.org/project/instatrace/)

**The most comprehensive Instagram OSINT tool — extract every possible detail from any Instagram profile.**

[Features](#features) · [Installation](#installation) · [Usage](#usage) · [Commands](#commands) · [Export](#export)

</div>

---

## ⚡ Features

### 🎯 Profile Intelligence
- **User ID & Username** — Resolve any username to numeric ID
- **Full Name, Bio, Pronouns** — Complete personal info
- **Account Type** — Personal / Business / Creator detection
- **Verification Status** — Blue badge, Meta Verified eligibility
- **Privacy Status** — Public / Private detection
- **Business Category** — Industry / niche classification
- **Account Age Estimation** — Approximate creation year from user ID

### 📊 Statistics & Analytics
- **Follower / Following Count** — Real-time numbers
- **Post Count** — Total media on profile
- **IGTV / Reels / AR Effects Count** — Content breakdown
- **Story Highlights Count** — Number of highlight reels
- **Engagement Rate** — Avg likes+comments per post / followers
- **Follower/Following Ratio Analysis** — Bot detection, influencer scoring

### 📧 Contact & Recovery Intelligence
- **Public Email** — Directly exposed email
- **Public Phone Number** — With country code
- **Phone Country Resolution** — Country, region, carrier lookup
- **Obfuscated Email** — Partial email from recovery flow (e.g., `j***n@g****.com`)
- **Obfuscated Phone** — Partial phone from recovery flow
- **WhatsApp Number & Link Status** — WhatsApp integration detection
- **City / Street Address / ZIP** — Business location data
- **Email/SMS/WhatsApp Reset Availability** — Recovery method detection

### 🖼️ Media Extraction
- **Timeline Posts** — With date filtering, pagination
- **Post Details** — Likes, comments, location, caption, media URLs
- **Story Highlights** — Highlight reels with titles and media counts
- **Tagged Posts** — Posts the user appears in
- **Comment Extraction** — Full comment data with user info
- **Media URLs** — HD image/video direct URLs

### 👥 Social Graph Analysis
- **Followers List** — Full extraction with pagination
- **Following List** — Full extraction with pagination
- **Mutual Followers** — Compare two accounts
- **Similar Accounts** — Instagram's suggested related profiles

### 🔗 External Intelligence
- **Bio Link Analysis** — DNS resolution, WHOIS data, domain info
- **Hashtag Intelligence** — Extract posts from any hashtag
- **Username Availability Check** — Existence verification

### 📦 Export & Reporting
- **JSON Export** — Complete structured data
- **CSV Export** — Spreadsheet-ready
- **TXT Export** — Human-readable reports
- **Auto-timestamped** — All exports organized in `instatrace_reports/`

---

## 🚀 Installation

### From PyPI
```bash
pip install instatrace
```

### From Source
```bash
git clone https://github.com/John-Varghese-EH/InstaTrace.git
cd InstaTrace
pip install -e .
```

### Dependencies Only
```bash
pip install -r requirements.txt
```

---

## 📖 Usage

### Quick Start
```bash
# Full profile intelligence
instatrace profile -u <username> -s <session_id>

# Full scan (runs ALL modules)
instatrace fullscan -u <username> -s <session_id>

# No session required
instatrace lookup -u <username>
instatrace check -u <username>
instatrace biolink --url https://example.com
```

### Getting Your Session ID
1. Log into Instagram in your browser
2. Open Developer Tools (F12) → Application → Cookies
3. Find `sessionid` cookie value
4. Use it with `-s` flag

### Run as Python Module
```bash
python -m instatrace profile -u <username> -s <session_id>
```

---

## 🛠️ Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `profile` | `p` | Full profile intelligence (ID, name, bio, stats, contacts, account type, engagement rate) |
| `lookup` | `l` | Advanced lookup — obfuscated email/phone from recovery |
| `posts` | `m` | Extract user's timeline posts with date filters |
| `post-info` | `pi` | Detailed info on a specific post |
| `followers` | `fl` | Extract full followers list |
| `following` | `fg` | Extract full following list |
| `mutual` | — | Find mutual followers between two users |
| `hashtag` | `ht` | Extract posts from a hashtag |
| `similar` | `sim` | Find Instagram-suggested similar accounts |
| `highlights` | `hl` | Extract story highlight reels |
| `tagged` | `tg` | Extract posts the user is tagged in |
| `comments` | `cm` | Extract comments from a post |
| `check` | `ck` | Check if a username exists |
| `biolink` | `bl` | Analyze external bio link (WHOIS, DNS) |
| `ratio` | `r` | Follower/following ratio analysis |
| `fullscan` | `fs` | Run ALL intelligence modules at once |

### Global Flags
```
-s, --session-id    Instagram session ID cookie
--sessions          Multiple session IDs for rotation (anti-rate-limit)
--proxy             Proxy URL (e.g., socks5://127.0.0.1:9050)
--export            Export format: json, csv, or txt
-v, --version       Show version
```

---

## 📤 Export

Append `--export json|csv|txt` to any command:

```bash
# Export profile to JSON
instatrace profile -u target -s SESSION --export json

# Export followers to CSV
instatrace followers -u target -s SESSION --export csv

# Full scan with TXT report
instatrace fullscan -u target -s SESSION --export txt
```

All exports are saved to `instatrace_reports/` with timestamps.

---

## 🔧 Advanced Usage

### Multi-Session Rotation (Anti-Rate-Limit)
```bash
instatrace followers -u target --sessions SID1 SID2 SID3
```

### Proxy Support
```bash
instatrace profile -u target -s SESSION --proxy socks5://127.0.0.1:9050
```

### Date-Filtered Posts
```bash
instatrace posts -u target -s SESSION --from-date 2024-01-01 --to-date 2024-12-31
```

### Mutual Follower Comparison
```bash
instatrace mutual -u user1 -u2 user2 -s SESSION --max 10000
```

---

## ⚠️ Disclaimer

This tool is designed for **authorized security research and educational purposes only**. Do not use this tool against accounts you do not own or have explicit permission to test. The author is not responsible for any misuse.

---

## 👤 Author

**John-Varghese-EH**

- GitHub: [@John-Varghese-EH](https://github.com/John-Varghese-EH)

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Built with ❤️ by [John-Varghese-EH](https://github.com/John-Varghese-EH)

</div>
