"""
Curated Drug Database
High-quality dataset of common formulation drugs with validated BCS classification
"""

CURATED_DRUGS = [
    # BCS Class I - High Solubility, High Permeability
    {
        "name": "Metoprolol",
        "cas": "37350-58-6",
        "molecular_weight": 267.36,
        "logp": 1.88,
        "logs": -2.0,
        "hbd": 2,
        "hba": 4,
        "tpsa": 50.7,
        "bcs_class": "BCS I",
        "bcs_reference": "FDA BCS Guidance",
        "indication": "Beta-blocker for hypertension and angina",
        "dose_mg": "25-100",
        "formulation_strategies": ["Immediate-release tablets", "Extended-release formulations"],
        "commercial_products": ["Lopressor", "Toprol-XL"]
    },
    {
        "name": "Propranolol",
        "cas": "525-66-6",
        "molecular_weight": 259.34,
        "logp": 3.48,
        "logs": -2.5,
        "hbd": 2,
        "hba": 3,
        "tpsa": 41.5,
        "bcs_class": "BCS I",
        "bcs_reference": "FDA BCS Guidance",
        "indication": "Beta-blocker for hypertension, angina, arrhythmia",
        "dose_mg": "10-80",
        "formulation_strategies": ["IR tablets", "SR capsules"],
        "commercial_products": ["Inderal", "InnoPran XL"]
    },
    {
        "name": "Caffeine",
        "cas": "58-08-2",
        "molecular_weight": 194.19,
        "logp": -0.07,
        "logs": -0.8,
        "hbd": 0,
        "hba": 6,
        "tpsa": 58.4,
        "bcs_class": "BCS I",
        "bcs_reference": "Literature",
        "indication": "CNS stimulant",
        "dose_mg": "100-200",
        "formulation_strategies": ["Tablets", "Capsules", "Beverages"],
        "commercial_products": ["Vivarin", "No-Doz"]
    },

    # BCS Class II - Low Solubility, High Permeability
    {
        "name": "Ibuprofen",
        "cas": "15687-27-1",
        "molecular_weight": 206.28,
        "logp": 3.97,
        "logs": -3.5,
        "hbd": 1,
        "hba": 2,
        "tpsa": 37.3,
        "bcs_class": "BCS II",
        "bcs_reference": "Lindenberg et al. Eur J Pharm Biopharm 2004",
        "indication": "NSAID for pain and inflammation",
        "dose_mg": "200-800",
        "formulation_strategies": ["Solid dispersion", "Salt (lysine, sodium)", "Nanocrystal"],
        "commercial_products": ["Advil", "Motrin", "Nurofen"]
    },
    {
        "name": "Naproxen",
        "cas": "22204-53-1",
        "molecular_weight": 230.26,
        "logp": 3.18,
        "logs": -3.2,
        "hbd": 1,
        "hba": 3,
        "tpsa": 46.5,
        "bcs_class": "BCS II",
        "bcs_reference": "Literature",
        "indication": "NSAID for pain and inflammation",
        "dose_mg": "250-500",
        "formulation_strategies": ["Sodium salt", "Solid dispersion"],
        "commercial_products": ["Aleve", "Naprosyn"]
    },
    {
        "name": "Celecoxib",
        "cas": "169590-42-5",
        "molecular_weight": 381.37,
        "logp": 3.47,
        "logs": -5.8,
        "hbd": 1,
        "hba": 5,
        "tpsa": 82.1,
        "bcs_class": "BCS II",
        "bcs_reference": "FDA dissolution data",
        "indication": "COX-2 inhibitor for arthritis",
        "dose_mg": "100-200",
        "formulation_strategies": ["Solid dispersion (PVP)", "Nanocrystal"],
        "commercial_products": ["Celebrex"]
    },
    {
        "name": "Griseofulvin",
        "cas": "126-07-8",
        "molecular_weight": 352.77,
        "logp": 2.18,
        "logs": -4.6,
        "hbd": 1,
        "hba": 6,
        "tpsa": 80.5,
        "bcs_class": "BCS II",
        "bcs_reference": "Classic BCS II example",
        "indication": "Antifungal",
        "dose_mg": "500",
        "formulation_strategies": ["Micronization", "Nanocrystal", "Solid dispersion"],
        "commercial_products": ["Grifulvin V"]
    },
    {
        "name": "Paclitaxel",
        "cas": "33069-62-4",
        "molecular_weight": 853.91,
        "logp": 3.0,
        "logs": -6.5,
        "hbd": 4,
        "hba": 14,
        "tpsa": 221.3,
        "bcs_class": "BCS IV",
        "bcs_reference": "Literature (poor solubility and permeability)",
        "indication": "Anticancer agent",
        "dose_mg": "IV only",
        "formulation_strategies": ["Cremophor formulation", "Albumin-bound nanoparticles", "Liposomal"],
        "commercial_products": ["Taxol", "Abraxane"]
    },
    {
        "name": "Ritonavir",
        "cas": "155213-67-5",
        "molecular_weight": 720.95,
        "logp": 5.6,
        "logs": -6.8,
        "hbd": 4,
        "hba": 11,
        "tpsa": 202.3,
        "bcs_class": "BCS IV",
        "bcs_reference": "Literature",
        "indication": "HIV protease inhibitor",
        "dose_mg": "100-600",
        "formulation_strategies": ["Hot-melt extrusion", "SEDDS", "ASD"],
        "commercial_products": ["Norvir"]
    },

    # BCS Class III - High Solubility, Low Permeability
    {
        "name": "Atenolol",
        "cas": "29122-68-7",
        "molecular_weight": 266.34,
        "logp": 0.16,
        "logs": -1.2,
        "hbd": 3,
        "hba": 5,
        "tpsa": 84.6,
        "bcs_class": "BCS III",
        "bcs_reference": "FDA BCS Guidance",
        "indication": "Beta-blocker for hypertension",
        "dose_mg": "25-100",
        "formulation_strategies": ["Permeation enhancers", "Standard tablets"],
        "commercial_products": ["Tenormin"]
    },
    {
        "name": "Metformin",
        "cas": "657-24-9",
        "molecular_weight": 129.16,
        "logp": -2.64,
        "logs": 0.5,
        "hbd": 2,
        "hba": 2,
        "tpsa": 91.5,
        "bcs_class": "BCS III",
        "bcs_reference": "FDA BCS Guidance",
        "indication": "Antidiabetic",
        "dose_mg": "500-2000",
        "formulation_strategies": ["IR/ER tablets", "HCl salt"],
        "commercial_products": ["Glucophage", "Fortamet"]
    },
    {
        "name": "Ranitidine",
        "cas": "66357-35-5",
        "molecular_weight": 314.40,
        "logp": 0.27,
        "logs": -0.5,
        "hbd": 1,
        "hba": 6,
        "tpsa": 86.5,
        "bcs_class": "BCS III",
        "bcs_reference": "Literature",
        "indication": "H2-receptor antagonist",
        "dose_mg": "150-300",
        "formulation_strategies": ["Standard tablets", "Effervescent tablets"],
        "commercial_products": ["Zantac"]
    },

    # BCS Class IV - Low Solubility, Low Permeability
    {
        "name": "Hydrochlorothiazide",
        "cas": "58-93-5",
        "molecular_weight": 297.74,
        "logp": -0.07,
        "logs": -3.4,
        "hbd": 3,
        "hba": 6,
        "tpsa": 135.0,
        "bcs_class": "BCS IV",
        "bcs_reference": "FDA BCS Guidance",
        "indication": "Diuretic for hypertension",
        "dose_mg": "12.5-50",
        "formulation_strategies": ["Micronization", "Combination products"],
        "commercial_products": ["Microzide"]
    },
    {
        "name": "Furosemide",
        "cas": "54-31-9",
        "molecular_weight": 330.74,
        "logp": 2.03,
        "logs": -3.4,
        "hbd": 3,
        "hba": 6,
        "tpsa": 131.8,
        "bcs_class": "BCS IV",
        "bcs_reference": "Literature",
        "indication": "Loop diuretic",
        "dose_mg": "20-80",
        "formulation_strategies": ["Micronization", "Salt formation", "Solid dispersion"],
        "commercial_products": ["Lasix"]
    },
]

def get_all_drugs():
    """获取所有策展药物"""
    return CURATED_DRUGS

def get_drugs_by_bcs_class(bcs_class):
    """按BCS分类筛选药物"""
    return [drug for drug in CURATED_DRUGS if drug['bcs_class'] == bcs_class]

def search_drugs(query):
    """搜索药物（名称或CAS）"""
    query_lower = query.lower()
    return [drug for drug in CURATED_DRUGS
            if query_lower in drug['name'].lower() or
            query_lower in drug.get('cas', '')]

def get_drug_by_name(name):
    """根据名称获取药物"""
    for drug in CURATED_DRUGS:
        if drug['name'].lower() == name.lower():
            return drug
    return None
