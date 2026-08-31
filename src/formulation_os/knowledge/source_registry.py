"""Source registry — the list of data sources as *registry*, not data.

Records, for every source, WHO the factual authority is, HOW we can actually
obtain it, its LICENCE, and its integration STATUS. This is deliberately kept
separate from the adapters so we always know provenance and access constraints
(e.g. which Chinese sources sit behind the 瑞数/RiskShield anti-bot wall).

Empirically verified (2026-08): the entire www.cde.org.cn and NMPA datasearch
respond with an anti-bot JS challenge (HTTP 202 + obfuscated 瑞数 token) to plain
HTTP clients — including CDE news/attachment paths — so none is fetchable with a
simple request. Those are marked access="anti_bot_riddler".
"""

from __future__ import annotations

from dataclasses import dataclass, field


# access methods
ACCESS_API = "api"                       # free programmatic JSON/REST
ACCESS_LOCAL_FILE = "local_file"         # public downloadable file -> parse offline
ACCESS_LOCAL_LICENCED = "local_licenced" # local file, licence-restricted
ACCESS_ANTIBOT = "anti_bot_riddler"      # 瑞数-walled; needs browser/manual
ACCESS_MANUAL = "manual"                 # human-in-the-loop download/export

# licence
LIC_PUBLIC = "public"                    # freely redistributable (e.g. US gov)
LIC_GOV_ARR = "gov_all_rights_reserved"  # gov site, "All Rights Reserved"
LIC_RESTRICTED = "restricted"            # third-party / licensed

# status
ST_INTEGRATED = "integrated"
ST_INTEGRATED_LOCAL = "integrated_local"   # integrated but local-only build
ST_PLANNED = "planned"
ST_BLOCKED = "blocked"


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    authority: str
    region: str                 # US | CN | EU | GLOBAL
    categories: tuple[str, ...]
    access: str
    licence: str
    status: str
    url: str = ""
    notes: str = ""


REGISTRY: list[Source] = [
    # ---- US / global (integrated) --------------------------------------------
    Source("PUBCHEM", "PubChem", "NIH/NLM", "GLOBAL",
           ("identity", "physicochemical"), ACCESS_API, LIC_PUBLIC, ST_INTEGRATED,
           "https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest"),
    Source("CHEMBL", "ChEMBL", "EMBL-EBI", "GLOBAL",
           ("identity", "physicochemical", "drug_forms"), ACCESS_API, LIC_PUBLIC, ST_INTEGRATED,
           "https://www.ebi.ac.uk/chembl/"),
    Source("OPENFDA", "openFDA Drugs@FDA", "US FDA", "US",
           ("approved_products",), ACCESS_API, LIC_PUBLIC, ST_INTEGRATED,
           "https://open.fda.gov/apis/"),
    Source("FDA_ORANGE_BOOK", "FDA Orange Book data files", "US FDA", "US",
           ("patents_exclusivity", "approved_products"), ACCESS_LOCAL_FILE, LIC_PUBLIC, ST_INTEGRATED,
           "https://www.fda.gov/media/76860/download"),
    Source("DRUGBANK", "DrugBank full DB", "DrugBank", "GLOBAL",
           ("identity", "physicochemical"), ACCESS_LOCAL_LICENCED, LIC_RESTRICTED, ST_INTEGRATED_LOCAL,
           "https://go.drugbank.com/", "Licence-restricted; local-only, never public/deploy."),

    # ---- China (planned; ordered by the agreed priority) ---------------------
    Source("CDE_MARKETED_CATALOG", "CDE 中国上市药品目录集", "NMPA/CDE", "CN",
           ("approved_products",), ACCESS_ANTIBOT, LIC_GOV_ARR, ST_PLANNED,
           "https://www.cde.org.cn/hymlj/index",
           "瑞数-walled (HTTP 202 + JS challenge). Acquire via manual browser export "
           "or third-party compilation; parse offline. PRIORITY 1 (25-drug validation)."),
    Source("CDE_REFERENCE_PRODUCT", "NMPA 仿制药参比制剂目录 (批次 .doc)", "NMPA/CDE", "CN",
           ("approved_products",), ACCESS_LOCAL_FILE, LIC_GOV_ARR, ST_INTEGRATED_LOCAL,
           "https://www.nmpa.gov.cn/directory/web/nmpa/images/",
           "Batch .doc attachments download directly from static nmpa.gov.cn paths "
           "(NOT 瑞数-walled), convert via textutil, parse the fixed 8-line table. "
           "INTEGRATED (local-only). Feed more batch URLs to raise coverage."),
    Source("CDE_LABEL", "CDE 药品说明书", "NMPA/CDE", "CN",
           ("product_label",), ACCESS_ANTIBOT, LIC_GOV_ARR, ST_PLANNED,
           "https://www.cde.org.cn/", "Separate product_label model. PRIORITY 3."),
    Source("NMPA_DRUG_QUERY", "NMPA 药品查询 (国产/进口)", "NMPA", "CN",
           ("approved_products",), ACCESS_ANTIBOT, LIC_GOV_ARR, ST_BLOCKED,
           "https://www.nmpa.gov.cn/datasearch/home-index.html",
           "Hardest 瑞数 site. Full CN drug universe. PRIORITY 4; do not attempt yet."),
    Source("CDE_CONSISTENCY", "CDE 一致性评价", "NMPA/CDE", "CN",
           ("consistency_evaluation",), ACCESS_ANTIBOT, LIC_GOV_ARR, ST_PLANNED,
           "https://www.cde.org.cn/", "Separate consistency_evaluation model."),
    Source("CDE_REVIEW", "CDE 审评查询", "NMPA/CDE", "CN",
           ("regulatory_history",), ACCESS_ANTIBOT, LIC_GOV_ARR, ST_PLANNED,
           "https://www.cde.org.cn/", "Separate regulatory_history model. PRIORITY 5."),

    # ---- phase 2 -------------------------------------------------------------
    Source("EPA_COMPTOX", "EPA CompTox", "US EPA", "US",
           ("physicochemical",), ACCESS_API, LIC_PUBLIC, ST_PLANNED,
           "https://www.epa.gov/comptox-tools", "Needs free CTX API key."),
    Source("EMA", "EMA medicines", "EU EMA", "EU",
           ("approved_products",), ACCESS_LOCAL_FILE, LIC_PUBLIC, ST_PLANNED,
           "https://www.ema.europa.eu/en/medicines/download-medicine-data"),
    Source("CSD", "CSD (CCDC)", "CCDC", "GLOBAL",
           ("drug_forms",), ACCESS_LOCAL_LICENCED, LIC_RESTRICTED, ST_PLANNED,
           "https://www.ccdc.cam.ac.uk/", "Licensed crystal structures."),
    Source("PATENTS_GLOBAL", "USPTO/Espacenet/WIPO/CNIPA", "multi", "GLOBAL",
           ("patents_exclusivity",), ACCESS_API, LIC_PUBLIC, ST_PLANNED,
           "", "Deep patent landscape beyond Orange Book."),
]

BY_ID = {s.id: s for s in REGISTRY}


def get(source_id: str) -> Source | None:
    return BY_ID.get(source_id)


def by_region(region: str) -> list[Source]:
    return [s for s in REGISTRY if s.region == region]
