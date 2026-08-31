"""Curated validation set for the local drug-intelligence database.

Deliberately small (start with ~25 well-characterised drugs, not thousands) so
each one can be validated end to end: identity, structure, physicochemical
properties, salt/crystal forms, US/China marketed products, patents, exclusivity
— each with its data source and any cross-source conflicts.

Chosen to span BCS classes and formulation archetypes (weak acids/bases,
high/low solubility, salts, poorly soluble => solid dispersion candidates).
Add names here and re-run ``scripts/build_drug_intelligence.py``.
"""

CURATED_DRUGS = [
    # NSAIDs / weak acids
    "Ibuprofen",
    "Aspirin",
    "Naproxen",
    "Diclofenac",
    "Celecoxib",
    # Antidiabetics
    "Metformin",
    "Glibenclamide",
    "Empagliflozin",
    # Poorly soluble / BCS II classics
    "Fenofibrate",
    "Itraconazole",
    "Griseofulvin",
    "Carbamazepine",
    "Nifedipine",
    # Weak bases / salts
    "Atorvastatin",
    "Amlodipine",
    "Sertraline",
    "Propranolol",
    # High-solubility / BCS I & III
    "Paracetamol",
    "Ranitidine",
    "Ciprofloxacin",
    # Oncology / kinase inhibitors (formulation-challenging)
    "Imatinib",
    "Gefitinib",
    # Others of formulation interest
    "Omeprazole",
    "Furosemide",
    "Warfarin",
]
