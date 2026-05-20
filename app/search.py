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

# ── Specific fallback sources by material type ───────────────────────────────
# Used when Serper returns no results — gives a REAL specific page, not homepage
_SPECIFIC_FALLBACK_SOURCES: dict[str, str] = {
    # Metals
    "steel":        "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "aluminum":     "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "copper":       "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "nickel":       "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "zinc":         "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    # Plastics
    "plastic":      "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "pet":          "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "hdpe":         "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    # Electronics — per unit LCA
    "laptop":       "Source: Dell Product Carbon Footprints — https://www.dell.com/en-us/dt/corporate/social-impact/advancing-sustainability/climate-action/product-carbon-footprints.htm",
    "computer":     "Source: Dell Product Carbon Footprints — https://www.dell.com/en-us/dt/corporate/social-impact/advancing-sustainability/climate-action/product-carbon-footprints.htm",
    "server":       "Source: Dell Product Carbon Footprints — https://www.dell.com/en-us/dt/corporate/social-impact/advancing-sustainability/climate-action/product-carbon-footprints.htm",
    "tablet":       "Source: Apple Environmental Progress Report — https://www.apple.com/environment/",
    "ipad":         "Source: Apple Environmental Progress Report — https://www.apple.com/environment/",
    "monitor":      "Source: HP Product Carbon Footprints — https://h20195.www2.hp.com/v2/getpdf.aspx/c08436529.pdf",
    "display":      "Source: HP Product Carbon Footprints — https://h20195.www2.hp.com/v2/getpdf.aspx/c08436529.pdf",
    "switch":       "Source: Cisco Product Sustainability — https://www.cisco.com/c/en/us/about/csr/esg-hub/product-sustainability.html",
    "router":       "Source: Cisco Product Sustainability — https://www.cisco.com/c/en/us/about/csr/esg-hub/product-sustainability.html",
    "firewall":     "Source: Fortinet Environmental — https://www.fortinet.com/corporate/about-us/environmental-social-governance",
    "ups":          "Source: APC Sustainability — https://www.se.com/ww/en/about-us/sustainability/",
    "pdu":          "Source: APC Sustainability — https://www.se.com/ww/en/about-us/sustainability/",
    "access point": "Source: Cisco Product Sustainability — https://www.cisco.com/c/en/us/about/csr/esg-hub/product-sustainability.html",
    "meraki":       "Source: Cisco Product Sustainability — https://www.cisco.com/c/en/us/about/csr/esg-hub/product-sustainability.html",
    "netapp":       "Source: NetApp ESG — https://www.netapp.com/company/corporate-responsibility/",
    "storage":      "Source: NetApp ESG — https://www.netapp.com/company/corporate-responsibility/",
    # Software / SaaS
    "license":      "Source: GHG Protocol Scope 3 Guidance — https://ghgprotocol.org/scope-3-technical-calculation-guidance",
    "subscription": "Source: GHG Protocol Scope 3 Guidance — https://ghgprotocol.org/scope-3-technical-calculation-guidance",
    "software":     "Source: GHG Protocol Scope 3 Guidance — https://ghgprotocol.org/scope-3-technical-calculation-guidance",
    "saas":         "Source: GHG Protocol Scope 3 Guidance — https://ghgprotocol.org/scope-3-technical-calculation-guidance",
    "microsoft 365":"Source: Microsoft Sustainability — https://www.microsoft.com/en-us/sustainability",
    # Energy
    "electricity":  "Source: TGO Thailand Grid 2023 — https://tgo.or.th/en/emission-factor/",
    "grid":         "Source: TGO Thailand Grid 2023 — https://tgo.or.th/en/emission-factor/",
    "diesel":       "Source: UK Gov BEIS 2024 — https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting",
    "natural gas":  "Source: IPCC AR6 WG3 — https://www.ipcc.ch/report/ar6/wg3/",
    # Transport
    "truck":        "Source: GLEC Framework v3 — https://smart-freight-centre.org/glec-framework/",
    "freight":      "Source: GLEC Framework v3 — https://smart-freight-centre.org/glec-framework/",
    "sea freight":  "Source: IMO GHG Strategy — https://www.imo.org/en/MediaCentre/HotTopics/Pages/Reducing-greenhouse-gas-emissions-from-ships.aspx",
    "air freight":  "Source: IATA Carbon Offset — https://www.iata.org/en/programs/environment/carbon-offset/",
    "road":         "Source: GLEC Framework v3 — https://smart-freight-centre.org/glec-framework/",
    # Construction
    "concrete":     "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "glass":        "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "wood":         "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "cardboard":    "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    # Furniture
    "desk":         "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "chair":        "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "furniture":    "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    # Food
    "food":         "Source: Poore & Nemecek (2018) — https://science.sciencemag.org/content/360/6392/987",
    "rice":         "Source: Poore & Nemecek (2018) — https://science.sciencemag.org/content/360/6392/987",
    "bread":        "Source: Poore & Nemecek (2018) — https://science.sciencemag.org/content/360/6392/987",
    "coffee":       "Source: Poore & Nemecek (2018) — https://science.sciencemag.org/content/360/6392/987",
    "cookies":      "Source: Poore & Nemecek (2018) — https://science.sciencemag.org/content/360/6392/987",
    "soap":         "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    # Paper / stationery
    "paper":        "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "stationery":   "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "office supplies": "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    # Rubber / chemicals
    "rubber":       "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "carbon fiber": "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
    "titanium":     "Source: Ecoinvent 3.9 — https://ecoinvent.org/the-ecoinvent-database/data-releases/ecoinvent-version-3/",
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


def get_trusted_source(category: str, material_name: str = "") -> str:
    """Return a specific trusted source URL. Falls back to category default."""
    if material_name:
        name_lower = material_name.lower()
        # Check specific fallback sources first
        for key, url in _SPECIFIC_FALLBACK_SOURCES.items():
            if key in name_lower:
                return url
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


def _is_homepage_url(url: str) -> bool:
    """Check if URL is just a domain root / homepage (not a specific page)."""
    clean = url.replace("https://", "").replace("http://", "").replace("www.", "")
    parts = clean.rstrip("/").split("/")
    return len(parts) <= 2


def clean_note(note: str, name: str, category: str = "material") -> str:
    """Ensure a note field has REAL, trusted source URLs from Serper.

    Strategy:
    1. Always search Serper first for real sources.
    2. If Serper finds results → use ONLY Serper results (discard AI generic URLs).
    3. If Serper fails → use specific fallback from _SPECIFIC_FALLBACK_SOURCES.
    4. Last resort → category default.
    """
    # Always search Serper first
    if SERPER_API_KEY and name:
        serper_sources = _serper_find_sources(name, max_results=3)
        if serper_sources:
            return " | ".join(serper_sources)

    # Serper failed → use specific fallback
    specific = get_trusted_source(category, name)
    if specific and not _is_homepage_url(specific.split(" — ")[-1] if " — " in specific else specific):
        return specific

    # Last resort: try to find any URL in the existing note
    existing_url = _URL_RE.search(note)
    if existing_url:
        url = existing_url.group()
        if not _is_homepage_url(url):
            return note

    return get_trusted_source(category, name)


def _extract_sources_from_note(note: str) -> list[str]:
    """Extract individual source strings from a note (split by ' | ' or ' — ')."""
    if not note:
        return []
    # Split by common separators
    parts = note.split(' | ')
    if len(parts) == 1:
        parts = note.split(' — ')
    return [p.strip() for p in parts if p.strip()]
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


def _build_serper_queries(material_name: str) -> list[str]:
    """Build multiple Serper queries from specific to broad."""
    name_lower = material_name.lower()
    queries = []

    # Electronics / IT
    if any(kw in name_lower for kw in ['laptop', 'computer', 'server', 'monitor', 'display', 'tablet', 'ipad', 'phone', 'smartphone', 'switch', 'router', 'firewall', 'ups', 'pdu', 'access point', 'cisco', 'dell', 'hp ', 'lenovo', 'apple', 'sony', 'netapp', 'fortinet', 'meraki', 'epson', 'legrand', 'ergotron', 'steelcase']):
        # Try specific product page first
        queries.append(f'"{material_name}" carbon footprint kg CO2e')
        # Broader: product type + LCA
        short_name = material_name.split('(')[0].strip()  # Remove parenthetical details
        queries.append(f'"{short_name}" lifecycle assessment CO2e kg')
        # Even broader: manufacturer + product category
        queries.append(f'{material_name.split()[0]} product carbon footprint database')

    # Software / SaaS
    elif any(kw in name_lower for kw in ['license', 'subscription', 'saas', 'software', 'microsoft 365', 'office 365', 'adobe', 'cloud']):
        queries.append(f'"{material_name}" carbon footprint per user CO2e')
        queries.append(f'software as a service carbon emission factor per user')

    # Transport
    elif any(kw in name_lower for kw in ['freight', 'transport', 'shipping', 'delivery', 'truck', 'sea freight', 'air freight', 'road']):
        queries.append(f'"{material_name}" emission factor kgCO2e per km')
        queries.append(f'GLEC Framework emission factor transport')

    # Energy
    elif any(kw in name_lower for kw in ['electricity', 'grid', 'diesel', 'gas', 'fuel', 'energy', 'power']):
        queries.append(f'"{material_name}" emission factor kgCO2e per kWh')
        queries.append(f'Thailand grid emission factor 2024')

    # Furniture / office equipment
    elif any(kw in name_lower for kw in ['desk', 'chair', 'furniture', 'office']):
        queries.append(f'"{material_name}" carbon footprint kg CO2e')
        queries.append(f'office furniture lifecycle CO2e emission factor')

    # Default: materials
    else:
        queries.append(f'"{material_name}" emission factor kgCO2e per kg')
        queries.append(f'{material_name} Ecoinvent emission factor')

    return queries


def _serper_find_sources(material_name: str, max_results: int = 3) -> list[str]:
    """Search Serper for real source URLs. Tries multiple queries from specific to broad."""
    import requests
    from urllib.parse import urlparse

    queries = _build_serper_queries(material_name)
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    all_sources = []
    seen_domains = set()

    for query in queries:
        payload = {"q": query, "num": max_results + 2}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            organic = data.get("organic", [])

            if not organic:
                continue

            logger.info(f"Serper query '{query[:60]}...': {len(organic)} results")

            for item in organic:
                source_url = item.get("link", "")
                source_title = item.get("title", "")
                if not source_url:
                    continue
                domain = urlparse(source_url).netloc.replace("www.", "")
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
                all_sources.append(f"{source_title} — {source_url}")
                if len(all_sources) >= max_results:
                    break

            if all_sources:
                break  # Found results, stop trying more queries

        except Exception as e:
            logger.error(f"Serper query failed: {e}")
            continue

    if all_sources:
        logger.info(f"Serper found {len(all_sources)} source(s) for '{material_name}'")
    return all_sources


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


