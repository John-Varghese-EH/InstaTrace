"""
InstaTrace Advanced Lookup Module — Obfuscated email/phone recovery, phone geo-resolution, bio link WHOIS.
Author: John-Varghese-EH
"""

import socket
from ..config import C, print_status, print_field, print_section, print_separator, bool_icon


def advanced_email_phone_lookup(api, username):
    """
    Perform an advanced lookup to extract obfuscated email/phone from Instagram's
    account recovery mechanism.

    Returns:
        dict: Lookup results including obfuscated email and phone.
    """
    print_status(f"Performing advanced lookup for @{username}...", "info")

    result = {
        "username": username,
        "obfuscated_email": None,
        "obfuscated_phone": None,
        "can_email_reset": None,
        "can_sms_reset": None,
        "can_whatsapp_reset": None,
        "has_valid_phone": None,
        "error": None,
    }

    resp = api.advanced_lookup(username)

    if not resp:
        result["error"] = "No response from lookup API"
        print_status("Lookup failed — no response", "error")
        return result

    if "error" in resp:
        result["error"] = resp.get("error")
        print_status(f"Lookup error: {resp.get('error')}", "error")
        return result

    if "message" in resp:
        if resp["message"] == "No users found":
            result["error"] = "No users found"
            print_status("User not found in lookup", "warning")
            return result

    # Extract obfuscated info
    result["obfuscated_email"] = resp.get("obfuscated_email")
    result["obfuscated_phone"] = resp.get("obfuscated_phone")
    result["can_email_reset"] = resp.get("can_email_reset")
    result["can_sms_reset"] = resp.get("can_sms_reset")
    result["can_whatsapp_reset"] = resp.get("can_whatsapp_reset")
    result["has_valid_phone"] = resp.get("has_valid_phone")

    # Additional parsing
    if resp.get("email_sent"):
        result["can_email_reset"] = True
    if resp.get("phone_number_sent"):
        result["can_sms_reset"] = True

    print_status("Advanced lookup complete", "success")
    return result


def resolve_phone_country(phone_number, country_code=None):
    """
    Resolve a phone number to its country of origin.

    Args:
        phone_number: Phone number string.
        country_code: Country dialing code (e.g., 1, 44, 91).

    Returns:
        dict: Phone info with country name.
    """
    result = {
        "phone": phone_number,
        "country_code": country_code,
        "country": None,
        "region": None,
        "carrier": None,
    }

    if not phone_number and not country_code:
        return result

    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier as pn_carrier
        from phonenumbers.phonenumberutil import region_code_for_country_code

        full_number = f"+{country_code} {phone_number}" if country_code else str(phone_number)
        parsed = phonenumbers.parse(full_number)

        import pycountry
        region = region_code_for_country_code(parsed.country_code)
        country = pycountry.countries.get(alpha_2=region)

        result["country"] = country.name if country else region
        result["region"] = geocoder.description_for_number(parsed, "en")
        result["carrier"] = pn_carrier.name_for_number(parsed, "en")

    except ImportError:
        result["error"] = "phonenumbers/pycountry not installed"
    except Exception as e:
        result["error"] = str(e)

    return result


def bio_link_analysis(url):
    """
    Analyze an external URL from a user's bio.
    Performs DNS lookup, WHOIS (if available), and basic reachability check.

    Args:
        url: The external URL to analyze.

    Returns:
        dict: Analysis results.
    """
    if not url:
        return None

    print_status(f"Analyzing bio link: {url}", "info")

    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]

    result = {
        "url": url,
        "domain": domain,
        "scheme": parsed.scheme,
        "path": parsed.path,
        "ip_address": None,
        "whois": None,
        "reachable": None,
    }

    # DNS Resolution
    try:
        ip = socket.gethostbyname(domain)
        result["ip_address"] = ip
    except socket.gaierror:
        result["ip_address"] = "Unresolvable"
    except Exception:
        pass

    # WHOIS Lookup
    try:
        import whois
        w = whois.whois(domain)
        result["whois"] = {
            "registrar": w.registrar,
            "creation_date": str(w.creation_date) if w.creation_date else None,
            "expiration_date": str(w.expiration_date) if w.expiration_date else None,
            "name_servers": w.name_servers if isinstance(w.name_servers, list) else [w.name_servers] if w.name_servers else [],
            "org": w.org,
            "country": w.country,
            "state": w.state,
            "city": w.city,
        }
    except ImportError:
        result["whois"] = {"error": "python-whois not installed (pip install python-whois)"}
    except Exception as e:
        result["whois"] = {"error": str(e)}

    # Reachability check
    try:
        import requests
        resp = requests.head(url, timeout=5, allow_redirects=True)
        result["reachable"] = resp.status_code < 400
        result["final_url"] = resp.url
        result["status_code"] = resp.status_code
    except:
        result["reachable"] = False

    print_status("Bio link analysis complete", "success")
    return result


# ═══════════════════════ DISPLAY ═══════════════════════

def display_lookup(result):
    """Display advanced lookup results."""
    if not result:
        return

    print_section("ADVANCED LOOKUP (Recovery Info)")
    print_field("Username", f"@{result.get('username')}")

    if result.get("error"):
        print_status(f"Error: {result['error']}", "error")
        return

    print_separator()

    if result.get("obfuscated_email"):
        print_field("Obfuscated Email", f"{C.SUCCESS}{result['obfuscated_email']}{C.RESET}")
    else:
        print_field("Obfuscated Email", f"{C.DIM}Not available{C.RESET}")

    if result.get("obfuscated_phone"):
        print_field("Obfuscated Phone", f"{C.SUCCESS}{result['obfuscated_phone']}{C.RESET}")
    else:
        print_field("Obfuscated Phone", f"{C.DIM}Not available{C.RESET}")

    print_separator()
    print_field("Email Reset Available", bool_icon(result.get("can_email_reset")))
    print_field("SMS Reset Available", bool_icon(result.get("can_sms_reset")))
    print_field("WhatsApp Reset", bool_icon(result.get("can_whatsapp_reset")))
    print_field("Has Valid Phone", bool_icon(result.get("has_valid_phone")))

    print()
    print_separator("═")


def display_phone_info(info):
    """Display phone country resolution results."""
    if not info:
        return

    print_section("PHONE NUMBER INTELLIGENCE")
    print_field("Phone Number", info.get("phone"))
    print_field("Country Code", info.get("country_code"))
    print_field("Country", info.get("country"))
    print_field("Region", info.get("region"))
    print_field("Carrier", info.get("carrier"))
    if info.get("error"):
        print_status(f"Note: {info['error']}", "warning")

    print()
    print_separator("═")


def display_bio_link(result):
    """Display bio link analysis results."""
    if not result:
        return

    print_section("BIO LINK ANALYSIS")
    print_field("URL", result.get("url"))
    print_field("Domain", result.get("domain"))
    print_field("IP Address", result.get("ip_address"))
    print_field("Reachable", bool_icon(result.get("reachable")))
    if result.get("final_url") and result["final_url"] != result["url"]:
        print_field("Redirects To", result["final_url"])
    if result.get("status_code"):
        print_field("HTTP Status", result["status_code"])

    whois_data = result.get("whois", {})
    if whois_data and "error" not in whois_data:
        print_separator()
        print_status("WHOIS Information:", "info")
        print_field("Registrar", whois_data.get("registrar"))
        print_field("Organization", whois_data.get("org"))
        print_field("Created", whois_data.get("creation_date"))
        print_field("Expires", whois_data.get("expiration_date"))
        print_field("Country", whois_data.get("country"))
        print_field("State", whois_data.get("state"))
        print_field("City", whois_data.get("city"))
        if whois_data.get("name_servers"):
            for i, ns in enumerate(whois_data["name_servers"][:5], 1):
                print_field(f"Nameserver #{i}", ns)
    elif whois_data and "error" in whois_data:
        print_status(f"WHOIS: {whois_data['error']}", "warning")

    print()
    print_separator("═")
