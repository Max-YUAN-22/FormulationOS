"""Curated deep-profile drug set for the drug-intelligence database.

These drugs get the FULL depth (US/CN marketed products, patents/exclusivity,
DrugBank pKa/logS, CN 参比制剂) — as opposed to the ~4,225 catalog drugs which
carry a lightweight identity+physicochemical profile only.

Chosen to be common and formulation-relevant, spanning therapeutic classes and
BCS classes (weak acids/bases, high/low solubility, salts, poorly-soluble
solid-dispersion candidates). Add names here and re-run
``scripts/build_drug_intelligence.py`` (+ import_cn_reference_drugfuture.py),
then ``scripts/prebuild_catalog_lite.py``.
"""

CURATED_DRUGS = [
    # ── NSAIDs / analgesics ──────────────────────────────────────────────
    "Ibuprofen", "Aspirin", "Naproxen", "Diclofenac", "Celecoxib",
    "Ketoprofen", "Indomethacin", "Meloxicam", "Piroxicam", "Etoricoxib",
    "Paracetamol", "Tramadol", "Morphine", "Codeine",
    # ── Cardiovascular / lipid / antithrombotic ──────────────────────────
    "Atorvastatin", "Simvastatin", "Rosuvastatin", "Pravastatin",
    "Amlodipine", "Nifedipine", "Diltiazem", "Verapamil",
    "Lisinopril", "Enalapril", "Valsartan", "Losartan", "Candesartan",
    "Metoprolol", "Bisoprolol", "Carvedilol", "Propranolol",
    "Clopidogrel", "Ticagrelor", "Warfarin", "Rivaroxaban", "Apixaban",
    "Furosemide", "Hydrochlorothiazide", "Spironolactone", "Digoxin",
    # ── Antidiabetics ────────────────────────────────────────────────────
    "Metformin", "Glibenclamide", "Gliclazide", "Glimepiride",
    "Empagliflozin", "Dapagliflozin", "Sitagliptin", "Pioglitazone",
    # ── CNS / psychiatry / neurology ─────────────────────────────────────
    "Sertraline", "Fluoxetine", "Paroxetine", "Escitalopram",
    "Venlafaxine", "Duloxetine", "Diazepam", "Alprazolam",
    "Quetiapine", "Olanzapine", "Risperidone", "Aripiprazole",
    "Gabapentin", "Pregabalin", "Levetiracetam", "Lamotrigine",
    "Carbamazepine", "Valproate", "Donepezil",
    # ── GI ───────────────────────────────────────────────────────────────
    "Omeprazole", "Esomeprazole", "Lansoprazole", "Pantoprazole",
    "Ranitidine", "Ondansetron",
    # ── Anti-infectives / antifungals / antivirals ───────────────────────
    "Amoxicillin", "Azithromycin", "Clarithromycin", "Ciprofloxacin",
    "Levofloxacin", "Doxycycline", "Metronidazole",
    "Fluconazole", "Itraconazole", "Voriconazole", "Griseofulvin",
    "Acyclovir", "Oseltamivir",
    # ── Respiratory / allergy ────────────────────────────────────────────
    "Montelukast", "Salbutamol", "Budesonide", "Cetirizine", "Loratadine",
    # ── Oncology / endocrine ─────────────────────────────────────────────
    "Imatinib", "Gefitinib", "Erlotinib", "Sorafenib",
    "Methotrexate", "Tamoxifen", "Letrozole", "Anastrozole", "Capecitabine",
    # ── Poorly-soluble / other formulation-interesting ───────────────────
    "Fenofibrate", "Sildenafil", "Tadalafil", "Ketoconazole",
    "Allopurinol", "Febuxostat", "Prednisolone", "Dexamethasone",
    "Levothyroxine", "Tamsulosin", "Finasteride",
]
