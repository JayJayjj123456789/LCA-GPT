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
    # หมวด 2.1: ฐานข้อมูลอุตสาหกรรม (researched fallback sources)
    "worldsteel.org",
    "international-aluminium.org",
    "internationalcopper.org",
    "nickelinstitute.org",
    "zinc.org",
    "plasticseurope.org",
    "glassforeurope.com",
    "nrmca.org",
    "base-empreinte.ademe.fr",
    "pmc.ncbi.nlm.nih.gov",
    "dell.com",
    "delltechnologies.com",
    "nvidia.com",
    "cisco.com",
    "ekonomiaisrodowisko.pl",
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

# ── Fallback emission factors — deep web-researched, GWP-100, with units ─────
# Units are stated in every source note and must match how amounts are used:
#   metals/plastics/construction  → kgCO2e per kg (cradle-to-gate, primary)
#   electronics                   → kgCO2e per unit (lifecycle unless noted)
#   energy                        → kgCO2e per kWh / per m3 / per litre
#   transport                     → kgCO2e per vehicle-km (bus/air/rail/ship
#                                    are per passenger-km / tonne-km as noted)
_FALLBACK_EF: dict[str, EfResult] = {
    # Metals (kgCO2e/kg, cradle-to-gate, primary)
    "steel":        EfResult(2.40,  "Source: worldsteel 2022 LCI — 2.4 kgCO2e per kg, cradle-to-gate (plate 2.47, range 2.2-2.6) — https://worldsteel.org/wp-content/uploads/Plate-Global-Construction.pdf"),
    "aluminum":     EfResult(14.8,  "Source: International Aluminium Institute 2023 — 14.8 kgCO2e per kg, primary ingot, cradle-to-gate (range 4.5-22 by grid mix) — https://international-aluminium.org/landing/aluminium-carbon-footprint-faqs/"),
    "copper":       EfResult(4.0,   "Source: International Copper Association 2019 global LCA — 4.0 kgCO2e per kg, cathode, cradle-to-gate (3,965 kg/t) — https://internationalcopper.org/"),
    "nickel":       EfResult(11.0,  "Source: Nickel Institute LCI FAQ 2020 — 11 kgCO2e per kg, class 1 Ni, cradle-to-gate (range 7.6-13) — https://nickelinstitute.org/media/4817/lifecycledata-faq-update2020.pdf"),
    "zinc":         EfResult(3.89,  "Source: International Zinc Association 2022 global LCA — 3.89 kgCO2e per kg, SHG zinc, cradle-to-gate — https://www.zinc.org/"),
    "titanium":     EfResult(36.0,  "Source: Norgate et al. 2007 (CSIRO) — 36 kgCO2e per kg, Kroll sponge, cradle-to-gate (range 25-51) — https://www.researchgate.net/publication/222402610"),
    "carbon fiber": EfResult(24.0,  "Source: Peer-reviewed meta-analysis 2023 — 24 kgCO2e per kg, PAN-based, cradle-to-gate (range 13-34) — https://pmc.ncbi.nlm.nih.gov/articles/PMC10780919/"),
    # Plastics / polymers (kgCO2e/kg, resin cradle-to-gate)
    "plastic":      EfResult(2.50,  "Source: DEFRA/BEIS 2023 — 2.5 kgCO2e per kg, mixed polymer incl. forming — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023"),
    "pet":          EfResult(2.50,  "Source: PlasticsEurope Eco-profile / esu-services 2026 — 2.5 kgCO2e per kg, PET resin, cradle-to-gate (range 2.1-2.7) — https://plasticseurope.org/"),
    "hdpe":         EfResult(1.90,  "Source: PlasticsEurope Eco-profile 2014 / ecoinvent 3.9.1 — 1.9 kgCO2e per kg, HDPE resin, cradle-to-gate (1.80-1.87) — https://plasticseurope.org/"),
    "rubber":       EfResult(2.50,  "Source: ADEME Base IMPACTS / GaBi — 2.5 kgCO2e per kg, natural+SBR rubber mix, cradle-to-gate — https://base-empreinte.ademe.fr/"),
    # Construction / packaging (kgCO2e/kg, cradle-to-gate)
    "glass":        EfResult(1.10,  "Source: Glass for Europe float-glass LCA — 1.1 kgCO2e per kg (float 1.23, container 0.95-1.25) — https://www.glassforeurope.com/"),
    "concrete":     EfResult(0.10,  "Source: NRMCA LCA / ÖKOBAUDAT 2024 — 0.10 kgCO2e per kg, ready-mix C30/37 (195-330 kg/m3 ÷ ~2,350 kg/m3) — https://www.nrmca.org/"),
    "wood":         EfResult(0.20,  "Source: ecoinvent 3.10 sawnwood / CORRIM 2024 — 0.20 kgCO2e per kg, sawn timber, cradle-to-gate (range 0.08-0.35, biogenic C excluded) — https://ecoinvent.org/"),
    "cardboard":    EfResult(1.20,  "Source: ecoinvent 3.10 containerboard / FEFCO 2023 — 1.2 kgCO2e per kg, corrugated, cradle-to-gate (range 1.0-1.5) — https://ecoinvent.org/"),
    "paper":        EfResult(1.30,  "Source: DEFRA 2023 — 1.3 kgCO2e per kg, office paper, cradle-to-mill-gate (1.35) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023"),
    # Electronics / equipment (kgCO2e per unit — lifecycle unless noted)
    "laptop":            EfResult(300.0,  "Source: Dell Latitude PCF + MDPI 2025 LCA — 300 kgCO2e per unit, 14-16in business laptop, full lifecycle (range 200-450) — https://www.dell.com/en-us/dt/corporate/social-impact/advancing-sustainability/climate-action/product-carbon-footprints.htm"),
    "computer":          EfResult(420.0,  "Source: Dell OptiPlex Tower 7010 PCF — 420 kgCO2e per unit, desktop tower, full lifecycle (426±110) — https://www.delltechnologies.com/asset/en-us/products/desktops-and-all-in-ones/technical-support/optiplex-tower-7010-pcf-datasheet.pdf"),
    "server":            EfResult(6300.0, "Source: Dell PowerEdge R710 PCF — 6,300 kgCO2e per unit, 1U rack server, full lifecycle (use = 64-90%; mfg ≈ 400-470) — https://www.dell.com/"),
    "computing hardware":EfResult(6300.0, "Source: Dell PowerEdge PCF / Cisco UCS — 6,300 kgCO2e per unit, rack server class, full lifecycle — https://www.dell.com/"),
    "electronics":       EfResult(30.0,   "Source: 196-product PCF study 2023 — 30 kgCO2e per unit, small IT device class (keyboard 14.5, webcam 5.4, monitor 179) — https://ekonomiaisrodowisko.pl/article/view/757"),
    "electronic equipment":EfResult(30.0, "Source: 196-product PCF study 2023 — 30 kgCO2e per unit, small IT device class — https://ekonomiaisrodowisko.pl/article/view/757"),
    "gpu":               EfResult(164.0,  "Source: NVIDIA HGX H100 PCF / arXiv 2509.00093 — 164 kgCO2e per unit, cradle-to-gate (A100 128-181; gaming GPUs 100-250) — https://images.nvidia.com/aem-dam/Solutions/documents/HGX-H100-PCF-Summary.pdf"),
    "stationery":        EfResult(1.10,   "Source: ecoinvent printed paper — 1.1 kgCO2e per kg, paper-based stationery, cradle-to-mill-gate — https://ecoinvent.org/"),
    "office supplies":   EfResult(1.10,   "Source: ecoinvent printed paper — 1.1 kgCO2e per kg, paper-based office supplies — https://ecoinvent.org/"),
    "office supplies & consumables": EfResult(1.10, "Source: ecoinvent printed paper — 1.1 kgCO2e per kg, paper-based consumables — https://ecoinvent.org/"),
    # Energy
    "electricity":  EfResult(0.4857, "Source: TGO Thailand Grid EF 2021 (announced May 2025) — 0.4857 kgCO2e per kWh, demand-side — https://ghgreduction.tgo.or.th/"),
    "natural gas":  EfResult(2.05,   "Source: UK DEFRA 2024 — 2.05 kgCO2e per m3 (0.183 kgCO2e/kWh gross CV) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "diesel":       EfResult(2.66,   "Source: UK DEFRA 2024 — 2.66 kgCO2e per litre, mineral diesel (2.51 avg blend) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    # Transport
    "truck":             EfResult(0.87,   "Source: UK DEFRA 2024 — 0.87 kgCO2e per vehicle-km, avg HGV (rigid 7.5-17t 0.59, >17t 0.98) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "passenger car":     EfResult(0.1645, "Source: UK DEFRA 2024 — 0.1645 kgCO2e per vehicle-km, avg petrol car — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "car":               EfResult(0.1645, "Source: UK DEFRA 2024 — 0.1645 kgCO2e per vehicle-km, avg petrol car — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "public bus":        EfResult(0.130,  "Source: UK DEFRA 2024 — 0.130 kgCO2e per passenger-km, local bus (occupancy built in) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "bus":               EfResult(0.130,  "Source: UK DEFRA 2024 — 0.130 kgCO2e per passenger-km, local bus — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "public bus / van":  EfResult(0.130,  "Source: UK DEFRA 2024 — 0.130 kgCO2e per passenger-km, local bus — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "van":               EfResult(0.079,  "Source: UK DEFRA 2024 — 0.079 kgCO2e per vehicle-km, avg van ≤3.5t (Class III 0.089) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "air travel":        EfResult(0.110,  "Source: UK DEFRA 2024 — 0.110 kgCO2e per passenger-km, short-haul incl. RFI uplift (0.1097) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "air":               EfResult(0.110,  "Source: UK DEFRA 2024 — 0.110 kgCO2e per passenger-km, short-haul — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "flight":            EfResult(0.110,  "Source: UK DEFRA 2024 — 0.110 kgCO2e per passenger-km, short-haul — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "ship":              EfResult(0.016,  "Source: UK DEFRA 2024 — 0.016 kgCO2e per tonne-km, container ship avg (bulk 0.0035, gen cargo 0.013) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "rail":              EfResult(0.028,  "Source: GLEC Framework v3 / DEFRA — 0.028 kgCO2e per tonne-km, rail freight (electric) — https://smart-freight-centre.org/glec-framework/"),
    "train":             EfResult(0.035,  "Source: UK DEFRA 2024 — 0.035 kgCO2e per passenger-km, national electric rail — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
    "motorcycle":        EfResult(0.114,  "Source: UK DEFRA 2024 — 0.114 kgCO2e per vehicle-km, avg motorcycle (small 0.083, large 0.133) — https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"),
}

# ── Broadened regex to catch real-world EF formats ───────────────────────────
_EF_PATTERN = re.compile(
    r"(\d+\.?\d*)\s*(?:"
    r"kg\s*CO[₂2]?[\s\-]?e(?:q(?:uivalent)?)?(?:[/\s]*kg)?"
    r"|kgCO2e?(?:/kg)?"
    r"|t(?:onnes?)?\s*CO[₂2][\s\-]?eq?"
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


def search_emission_factor(material_name: str) -> EfResult | None:
    """Search for the latest emission factor of a material.

    Priority:
    1. Local fallback database (exact + fuzzy name matching) — free, instant
    2. Serper.dev (Google Search) — only if key set AND material not found locally

    Returns:
        EfResult with value + source URL, or None if not found
    """
    if not material_name or not material_name.strip():
        return None

    # Check local fallback first — saves Serper credits and is deterministic
    key = _match_fallback_key(material_name)
    if key is not None:
        logger.info(
            f"Using fallback EF for '{material_name}' -> '{key}': {_FALLBACK_EF[key].value}"
        )
        return _FALLBACK_EF[key]

    # Only hit Serper for truly unknown materials
    if SERPER_API_KEY:
        result = _serper_search(material_name)
        if result:
            return result

    logger.warning(f"No EF found for '{material_name}'")
    return None


# ── Fuzzy fallback-key matching ──────────────────────────────────────────────
# Maps transport/energy phrasings to their canonical fallback key so compound
# names like "Road Freight" resolve to "truck" instead of hitting Serper.
_KEY_ALIASES: dict[str, str] = {
    "air freight":   "air",
    "sea freight":   "ship",
    "ocean freight": "ship",
    "road freight":  "truck",
    "freight":       "truck",
    "road":          "truck",
    "shipping":      "ship",
    "grid":          "electricity",
    "power":         "electricity",
    "fuel":          "diesel",
}

_SINGLE_TOKEN_KEYS = [k for k in _FALLBACK_EF if " " not in k]
_MULTI_WORD_KEYS    = [k for k in _FALLBACK_EF if " " in k]


def _match_fallback_key(name: str) -> str | None:
    """Return the best _FALLBACK_EF key for a (possibly compound) item name.

    Priority:
      1. Exact full-name match
      2. Transport/energy aliases (e.g. "road freight" → truck)
      3. Tokens inside parentheses (e.g. "Plastic Pellets (HDPE)" → hdpe)
      4. Whole-token match against single-word keys (e.g. "Steel Sheets" → steel)
      5. Multi-word keys as a substring (e.g. "natural gas" pipeline → natural gas)
      6. Single-word key contained in a longer token (e.g. "plastics" → plastic)

    Single-word keys are matched as whole tokens so short keys like "air" or
    "car" never match inside unrelated words ("chair", "cardboard").
    """
    normalized = name.lower().strip()
    if normalized in _FALLBACK_EF:
        return normalized

    for alias, key in _KEY_ALIASES.items():
        if alias in normalized:
            return key

    tokens = [t for t in re.split(r"[^a-z0-9]+", normalized) if t]

    paren_match = re.search(r"\(([^)]*)\)", normalized)
    paren_tokens = []
    if paren_match:
        paren_tokens = [t for t in re.split(r"[^a-z0-9]+", paren_match.group(1)) if t]

    single_keys = set(_SINGLE_TOKEN_KEYS)

    for t in paren_tokens:
        if t in single_keys:
            return t

    for t in tokens:
        if t in single_keys:
            return t

    for key in _MULTI_WORD_KEYS:
        if key in normalized:
            return key

    for t in paren_tokens + tokens:
        for key in single_keys:
            if len(key) >= 4 and key in t:
                return key

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


