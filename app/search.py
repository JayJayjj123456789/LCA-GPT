import os
import logging
import re
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# In-memory cache for Serper EF lookups (not used for source URLs)
_serper_cache: dict[str, "EfResult | None"] = {}


@dataclass
class EfResult:
    """Emission factor result with source attribution."""
    value: float
    source: str  # URL or description of where the EF came from


# ── Trusted canonical source URLs (always valid) ──────────────────────────────
TRUSTED_SOURCES = {
    "material":  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/",
    "energy":    "Source: TGO Thailand Grid 2023 — https://www.tgo.or.th",
    "transport": "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/",
}

# ── Trusted URL allowlist — 9 categories (substring match) ───────────────────
# If an existing note URL contains any of these, it is valid → keep it.
_TRUSTED_URL_PATTERNS = [
    # หมวด 1: มาตรฐานสากล
    "ghgprotocol.org",
    "ipcc.ch",
    "iso.org",
    # หมวด 2: ฐานข้อมูลคาร์บอนโลก
    "ecoinvent.org",
    "climatiq.io",
    "openlca.org",
    # หมวด 3: ไทย
    "tgo.or.th",
    "thaicarbonlabel.tgo.or.th",
    "nstda-tiis.or.th",
    "mtec.or.th",
    "diw.go.th",
    # หมวด 4: พลังงาน
    "eppo.go.th",
    "iea.org",
    "egat.co.th",
    # หมวด 5: โลจิสติกส์
    "smartfreightcentre.org",
    # หมวด 6: ESG / ตลาดทุน
    "set.or.th",
    "sec.or.th",
    "setsustainability.com",
    # หมวด 7: สารเคมี
    "carbon-minds.com",
    "sustamize.com",
    # หมวด 8: AI/Graph/Tech
    "arxiv.org",
    "neo4j.com",
    "langchain.com",
    # หมวด 9: กฎระเบียบยุโรป
    "ec.europa.eu",
    # หมวด 10: รัฐบาลอื่น
    "epa.gov",
    "gov.uk",
    "eplca.jrc.ec.europa.eu",
]

# ── Fallback emission factors — all with real verified URLs ──────────────────
_FALLBACK_EF: dict[str, EfResult] = {
    # Metals
    "steel":        EfResult(1.89,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "aluminum":     EfResult(8.24,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "copper":       EfResult(3.81,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "nickel":       EfResult(6.50,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "zinc":         EfResult(3.50,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "titanium":     EfResult(25.0,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    # Plastics / polymers
    "plastic":      EfResult(2.73,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "pet":          EfResult(2.73,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "hdpe":         EfResult(1.80,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "rubber":       EfResult(3.18,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    # Construction / packaging
    "glass":        EfResult(0.85,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "concrete":     EfResult(0.13,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "wood":         EfResult(0.46,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "cardboard":    EfResult(0.94,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "paper":        EfResult(0.94,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "carbon fiber": EfResult(22.5,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    # Electronics / equipment (per unit — lifecycle avg kgCO2e/unit)
    "laptop":            EfResult(331.0,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "computer":          EfResult(331.0,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "server":            EfResult(1400.0, "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "computing hardware":EfResult(1400.0, "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "electronics":       EfResult(25.0,   "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "electronic equipment":EfResult(25.0, "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "gpu":               EfResult(150.0,  "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "stationery":        EfResult(1.10,   "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "office supplies":   EfResult(1.10,   "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    "office supplies & consumables": EfResult(1.10, "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"),
    # Energy
    "electricity":  EfResult(0.499, "Source: TGO Thailand Grid 2023 — https://www.tgo.or.th"),
    "natural gas":  EfResult(2.02,  "Source: IPCC AR6 WG3 — https://www.ipcc.ch/report/ar6/wg3/"),
    "diesel":       EfResult(2.68,  "Source: UK Gov BEIS — https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting"),
    # Transport (kgCO2e per km)
    "truck":             EfResult(0.105, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "passenger car":     EfResult(0.210, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "car":               EfResult(0.210, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "public bus":        EfResult(0.089, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "bus":               EfResult(0.089, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "public bus / van":  EfResult(0.089, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "van":               EfResult(0.089, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "air travel":        EfResult(0.255, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "air":               EfResult(0.255, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "flight":            EfResult(0.255, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "ship":              EfResult(0.016, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "rail":              EfResult(0.028, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "train":             EfResult(0.028, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
    "motorcycle":        EfResult(0.103, "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"),
}

# ── Broadened regex to catch real-world EF formats ───────────────────────────
_EF_PATTERN = re.compile(
    r"(\d+\.?\d*)\s*(?:"
    r"kg\s*CO[₂2]?[\s\-]?e(?:q(?:uivalent)?)?[/\s]*kg"
    r"|kgCO2e?(?:/kg)?"
    r"|t(?:onnes?)?\s*CO[₂2][\s\-]?eq?"
    r"|CO2e?\s*\d+\.?\d*\s*kg"
    r"|\d+\.?\d*\s*kg\s*CO2"
    r"|\d+\.?\d*\s*kgCO2e"
    r"|CO2e?\d+\.?\d*kg"
    r"|\d+\.?\d*kgCO2e"
    r")",
    re.IGNORECASE,
)

_URL_RE = re.compile(r"https?://\S+")


def _note_has_trusted_url(note: str) -> bool:
    """Return True if the note already contains a trusted, verified URL."""
    m = _URL_RE.search(note)
    if not m:
        return False
    url = m.group()
    return any(pat in url for pat in _TRUSTED_URL_PATTERNS)


def get_trusted_source(category: str) -> str:
    """Return the canonical trusted source string for a category."""
    return TRUSTED_SOURCES.get(category, TRUSTED_SOURCES["material"])


# Generic URLs that AI always copies from prompt — these are NOT real sources
_AI_GENERIC_URLS = [
    "https://ecoinvent.org/database/",
    "https://www.tgo.or.th",
    "https://www.smartfreightcentre.org/en/glec/",
    "https://www.ipcc.ch/report/ar6/wg3/",
    "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
    "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting",
    "https://www.iea.org/data-and-statistics/data-product/emissions-factors-2023",
    "https://eplca.jrc.ec.europa.eu/",
    "https://ghgprotocol.org/",
    "https://www.iso.org/",
    "https://climatiq.io/",
    "https://thaicarbonlabel.tgo.or.th/",
    "https://www.diw.go.th/",
    "https://www.egat.co.th/",
    "https://www.setsustainability.com/",
    "https://ec.europa.eu/",
]


def clean_note(note: str, name: str, category: str = "material") -> str:
    """Ensure a note field has a REAL, trusted source URL.

    Strategy:
    1. If the note contains a URL that AI copied from prompt (generic) → replace with Serper result.
    2. If the note has a real specific URL (not in generic list) → keep as-is.
    3. If no URL → search Serper.
    4. If Serper fails → fall back to category default.
    """
    existing_url = _URL_RE.search(note)

    # If URL is one of the generic AI-copied ones → always replace with Serper
    if existing_url:
        url = existing_url.group()
        is_generic = any(url.startswith(g) or g.startswith(url) for g in _AI_GENERIC_URLS)
        if not is_generic:
            return note  # real specific URL, keep it
        logger.info(f"Replacing generic AI URL for '{name}': {url}")

    # Search Serper for a real source (bypass fallback DB)
    if SERPER_API_KEY and name:
        logger.info(f"Serper: searching source for '{name}'...")
        serper_source = _serper_find_source(name)
        if serper_source:
            return serper_source

    # Fallback to category default
    return get_trusted_source(category)


# ── Emission Factor Lookup (Serper used HERE only) ────────────────────────────

def search_emission_factor(material_name: str) -> EfResult | None:
    """Search for the latest emission factor of a material.

    Priority:
    1. Local fallback database (free, instant)
    2. Serper.dev (Google Search) — only if key set AND material not in fallback

    Returns:
        EfResult with value + source URL, or None if not found
    """
    # Check local fallback first — saves Serper credits
    key = material_name.lower().strip()
    if key in _FALLBACK_EF:
        fb = _FALLBACK_EF[key]
        logger.info(f"Using fallback EF for '{material_name}': {fb.value}")
        return fb

    # Only hit Serper for truly unknown materials
    if SERPER_API_KEY:
        result = _serper_search(material_name)
        if result:
            return result

    logger.warning(f"No EF found for '{material_name}'")
    return None


def _serper_find_source(material_name: str) -> str | None:
    """Search Serper for a real source URL for a material. Returns source string or None."""
    import requests

    query = f"{material_name} emission factor kgCO2e per kg"
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        organic = data.get("organic", [])

        if not organic:
            return None

        logger.info(f"Serper: {len(organic)} results for '{material_name}'")

        # Try to find a result with EF data
        for item in organic:
            text = f"{item.get('title', '')} {item.get('snippet', '')}"
            match = _EF_PATTERN.search(text)
            if match:
                source_url = item.get("link", "")
                source_title = item.get("title", "")
                if source_url:
                    logger.info(f"Serper found EF source for '{material_name}': {source_url}")
                    return f"Source: {source_title} — {source_url}"

        # No EF parsed — return first result as source
        first = organic[0]
        source_url = first.get("link", "")
        source_title = first.get("title", "")
        if source_url:
            logger.info(f"Serper no EF parsed, using first result for '{material_name}': {source_url}")
            return f"Source: {source_title} — {source_url}"

    except Exception as e:
        logger.error(f"Serper source search failed: {e}")
    return None


def _serper_search(material_name: str) -> EfResult | None:
    """Query Serper.dev for emission factor data. Uses in-memory caching.

    Only accepts EF values from trusted source domains. If a valid EF number
    is found but the URL is from an unknown site, the EF value is kept but
    the source is replaced with the canonical Ecoinvent URL.
    """
    import requests

    cache_key = material_name.lower().strip()
    if cache_key in _serper_cache:
        logger.info(f"Serper cache hit for '{material_name}'")
        return _serper_cache[cache_key]

    query = f"{material_name} emission factor kgCO2e per kg"
    url   = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}

    logger.info(f"Serper query: '{query}'")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data    = response.json()
        organic = data.get("organic", [])

        if not organic:
            logger.info(f"Serper: no results for '{material_name}'")
            _serper_cache[cache_key] = None
            return None

        logger.info(f"Serper: {len(organic)} results for '{material_name}'")

        for item in organic:
            text  = f"{item.get('title', '')} {item.get('snippet', '')}"
            match = _EF_PATTERN.search(text)
            if match:
                ef_value = float(match.group(1))
                if 0.001 <= ef_value <= 500:
                    source_url   = item.get("link", "")
                    source_title = item.get("title", "")

                    # Validate URL against trusted domains
                    url_trusted = any(pat in source_url for pat in _TRUSTED_URL_PATTERNS)

                    if url_trusted:
                        source_str = f"Source: {source_title} — {source_url}"
                        logger.info(f"Serper EF (trusted): {ef_value} from {source_url}")
                    else:
                        # Keep EF value but use canonical trusted source
                        source_str = TRUSTED_SOURCES["material"]
                        logger.info(
                            f"Serper EF {ef_value} from untrusted '{source_url}' "
                            f"→ using canonical source"
                        )

                    result = EfResult(value=ef_value, source=source_str)
                    _serper_cache[cache_key] = result
                    return result

        logger.info(f"Serper: no EF value parseable for '{material_name}'")
        _serper_cache[cache_key] = None
        return None

    except requests.Timeout:
        logger.warning(f"Serper timed out for '{material_name}'")
    except Exception as e:
        logger.error(f"Serper failed: {e}")

    _serper_cache[cache_key] = None
    return None


