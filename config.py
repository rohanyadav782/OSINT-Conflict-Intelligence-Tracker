"""Central configuration for the OSINT Conflict Tracker."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "conflict_tracker.db"

# API Keys
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")

# Search queries for conflict tracking
SEARCH_QUERIES = [
    "Iran Israel military",
    "Iran United States conflict",
    "Iran nuclear IAEA",
    "IRGC Israel",
    "Iran sanctions",
    "Iran proxy militia",
    "Hezbollah Israel",
    "Houthi Red Sea",
    "Iran cyber attack",
]

# RSS Feed URLs
RSS_FEEDS = {
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC Middle East": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
    "Times of Israel": "https://www.timesofisrael.com/feed/",
    "IRNA": "https://en.irna.ir/rss",
    "Reuters World": "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best",
    "US State Dept": "https://www.state.gov/rss-feed/press-releases/feed/",
}

# GDELT API
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# NewsAPI
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Known actors for entity matching
KNOWN_ACTORS = {
    # Iran
    "Iran": "Iran", "IRGC": "IRGC", "Islamic Revolutionary Guard Corps": "IRGC",
    "Quds Force": "IRGC Quds Force", "Iranian military": "Iran Military",
    "Khamenei": "Iran Leadership", "Raisi": "Iran Leadership",
    # Israel
    "Israel": "Israel", "IDF": "IDF", "Israel Defense Forces": "IDF",
    "Mossad": "Mossad", "Netanyahu": "Israel Leadership",
    "Israeli Air Force": "IAF", "Shin Bet": "Shin Bet",
    # United States
    "United States": "United States", "US": "United States", "USA": "United States",
    "Pentagon": "US Military", "CENTCOM": "US CENTCOM",
    "US Navy": "US Navy", "Biden": "US Leadership", "Trump": "US Leadership",
    # Proxies / Non-state
    "Hezbollah": "Hezbollah", "Hamas": "Hamas", "Houthi": "Houthis",
    "Ansar Allah": "Houthis", "Islamic Jihad": "Palestinian Islamic Jihad",
    "PMF": "Iraqi PMF", "Popular Mobilization Forces": "Iraqi PMF",
    # International
    "IAEA": "IAEA", "UN": "United Nations", "United Nations": "United Nations",
    "EU": "European Union", "NATO": "NATO",
}

# Event type classification keywords
EVENT_TYPE_KEYWORDS = {
    "military_action": [
        "strike", "attack", "bomb", "missile", "drone", "troops", "offensive",
        "airstrike", "shelling", "raid", "intercept", "launch", "fire", "combat",
        "killed", "destroyed", "targeted", "operation", "assault", "war",
    ],
    "diplomatic": [
        "negotiate", "talks", "summit", "agreement", "treaty", "envoy",
        "diplomacy", "dialogue", "ceasefire", "peace", "mediation", "ambassador",
    ],
    "sanctions": [
        "sanction", "embargo", "restrict", "freeze", "blacklist", "designat",
        "penalty", "trade ban", "economic pressure",
    ],
    "cyber": [
        "hack", "cyber", "malware", "breach", "digital", "ransomware",
        "espionage", "infrastructure attack",
    ],
    "nuclear": [
        "nuclear", "enrichment", "centrifuge", "IAEA", "uranium", "warhead",
        "plutonium", "atomic", "nonproliferation", "JCPOA",
    ],
    "rhetoric": [
        "warn", "threaten", "condemn", "denounce", "vow", "retaliate",
        "rhetoric", "statement", "declare", "promise", "pledge",
    ],
    "humanitarian": [
        "civilian", "casualt", "refugee", "humanitarian", "displaced",
        "aid", "crisis", "evacuat", "hospital", "infrastructure",
    ],
}

# Domain mapping from event types
EVENT_TYPE_TO_DOMAIN = {
    "military_action": "military",
    "diplomatic": "political",
    "sanctions": "economic",
    "cyber": "cyber",
    "nuclear": "nuclear",
    "rhetoric": "political",
    "humanitarian": "humanitarian",
}

# Severity base scores by event type
SEVERITY_BASE = {
    "military_action": 8.0,
    "nuclear": 9.0,
    "humanitarian": 7.0,
    "cyber": 6.0,
    "sanctions": 5.0,
    "rhetoric": 4.0,
    "diplomatic": 3.0,
}

# High-intensity keywords for severity scoring
HIGH_INTENSITY_KEYWORDS = [
    "war", "casualties", "invasion", "nuclear", "killed", "destroyed",
    "bombing", "massacre", "escalation", "retaliation", "ballistic",
    "chemical", "biological", "occupation", "genocide",
]

# Source reliability base scores
SOURCE_RELIABILITY = {
    "rss": 0.7,
    "news_api": 0.7,
    "gdelt": 0.75,
    "government": 0.65,
    "think_tank": 0.7,
    "acled": 0.9,
}

# Deduplication thresholds
DEDUP_FUZZY_THRESHOLD = 75  # rapidfuzz score
DEDUP_TFIDF_THRESHOLD = 0.85  # cosine similarity
DEDUP_TIME_WINDOW_HOURS = 48

# Conflict-related country filter keywords
CONFLICT_KEYWORDS = [
    "iran", "israel", "united states", "us ", "american",
    "hezbollah", "hamas", "houthi", "irgc", "idf",
    "tehran", "tel aviv", "jerusalem", "gaza", "beirut",
    "yemen", "syria", "iraq", "lebanon", "persian gulf",
    "strait of hormuz", "red sea", "golan",
]
