#!/usr/bin/env python3
import os
import re
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuration from environment variables
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
NOTIFY_UPDATES = os.environ.get("NOTIFY_UPDATES", "true").lower() in ("true", "1", "yes")

# NHC RSS Feeds (Only tracking the Atlantic basin)
FEEDS = {
    "Atlantic": "https://www.nhc.noaa.gov/index-at.xml",
}

STATE_FILE = "last_seen.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                # Ensure structure is correct
                if "seen_guids" not in state:
                    state["seen_guids"] = []
                if "seen_storms" not in state:
                    state["seen_storms"] = []
                return state
        except Exception as e:
            print(f"Error reading state file: {e}. Reinitializing.")
    return {"seen_guids": [], "seen_storms": []}

def save_state(state):
    # Keep lists bounded in size to prevent file from growing too large
    # Keep last 500 GUIDs and last 100 storms
    state["seen_guids"] = state["seen_guids"][-500:]
    state["seen_storms"] = state["seen_storms"][-100:]
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

def send_notification(title, message, link, priority="default", tags=""):
    if not NTFY_TOPIC:
        print(f"[Log] No NTFY_TOPIC configured. Would have sent: {title} - {message} ({link})")
        return
    
    url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": priority,
        "Tags": tags,
    }
    if link:
        headers["Click"] = link

    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Notification sent successfully: {title}")
    except Exception as e:
        print(f"Failed to send notification via ntfy.sh: {e}")

def extract_storm_info(title):
    prefixes = [
        "Potential Tropical Cyclone",
        "Post-Tropical Cyclone",
        "Subtropical Storm",
        "Subtropical Depression",
        "Tropical Depression",
        "Tropical Storm",
        "Hurricane",
        "Remnants of"
    ]
    title_clean = re.sub(r'\s+', ' ', title).strip()
    for prefix in prefixes:
        # Match case-insensitively
        if title_clean.lower().startswith(prefix.lower()):
            rest = title_clean[len(prefix):].strip()
            words = rest.split()
            if words:
                storm_name = words[0].upper()
                # Remove punctuation
                storm_name = re.sub(r'[^A-Z0-9\-]', '', storm_name)
                # Ensure it's not a generic word like "ADVISORY"
                if storm_name not in ("ADVISORY", "FORECAST", "PUBLIC", "UPDATE", "NUMBER"):
                    return prefix, storm_name
    return None, None

def check_feeds():
    state = load_state()
    state_changed = False
    
    print(f"Checking NHC feeds at {datetime.now().isoformat()}...")
    
    current_year = datetime.now().year
    
    for basin, url in FEEDS.items():
        print(f"Fetching {basin} feed: {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NHC Monitor)"})
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            
            for item in items:
                title = item.find("title").text or ""
                link = item.find("link").text or ""
                guid = item.find("guid").text or link
                description = item.find("description").text or ""
                
                # Clean up description (strip HTML tags)
                description_clean = re.sub(r'<[^>]*>', ' ', description)
                description_clean = re.sub(r'\s+', ' ', description_clean).strip()
                if len(description_clean) > 200:
                    description_clean = description_clean[:197] + "..."
                
                # Ignore non-storm items
                if "no tropical cyclones at this time" in title.lower():
                    continue
                if "tropical weather outlook" in title.lower():
                    continue
                
                prefix, storm_name = extract_storm_info(title)
                if not storm_name:
                    continue
                
                # Create a unique ID for this storm in this season/basin
                storm_id = f"{current_year}_{basin.upper()}_{storm_name}"
                
                # 1. Check if it's a completely new storm
                if storm_id not in state["seen_storms"]:
                    print(f"New storm detected: {prefix} {storm_name} in {basin} basin!")
                    state["seen_storms"].append(storm_id)
                    state["seen_guids"].append(guid)
                    state_changed = True
                    
                    # Send alert
                    send_notification(
                        title=f"🚨 New Storm: {prefix} {storm_name}",
                        message=f"A new storm ({prefix} {storm_name}) has formed in the {basin} basin. {description_clean}",
                        link=link,
                        priority="urgent",
                        tags="rotating_light,cyclone,warning"
                    )
                
                # 2. If it's an existing storm, check if this is a new advisory
                elif guid not in state["seen_guids"]:
                    state["seen_guids"].append(guid)
                    state_changed = True
                    
                    if NOTIFY_UPDATES:
                        print(f"New advisory for {storm_name}: {title}")
                        send_notification(
                            title=f"🌀 Update: {storm_name}",
                            message=title,
                            link=link,
                            priority="default",
                            tags="cyclone"
                        )
                    else:
                        print(f"New advisory for {storm_name} skipped (updates disabled): {title}")
                        
        except urllib.error.URLError as e:
            print(f"Network error fetching {basin} feed: {e}")
        except ET.ParseError as e:
            print(f"XML parse error for {basin} feed: {e}")
        except Exception as e:
            print(f"Unexpected error checking {basin} feed: {e}")
            
    if state_changed:
        save_state(state)
    else:
        print("No new storms or updates detected.")

if __name__ == "__main__":
    check_feeds()
