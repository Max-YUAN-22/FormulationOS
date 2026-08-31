"""PubChem adapter — primary source for drug identity and physicochemical data.

Uses the public PUG REST API (no key required):
https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest

Primary for:
  - identity        (CID, IUPAC name, formula, SMILES, InChI, InChIKey)
  - physicochemical (MW, XLogP, TPSA, HBD, HBA, rotatable bonds)

Physchem descriptors from PubChem are computed, so XLogP/TPSA are tagged
``PREDICTED``; formula/MW/counts are ``RECORDED`` from the deposited structure.
"""

from __future__ import annotations

from typing import Optional

import requests

from .base import SourceAdapter
from .schema import (
    CATEGORY_IDENTITY,
    CATEGORY_PHYSCHEM,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
)

_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
_PROPS = [
    "MolecularFormula",
    "MolecularWeight",
    "CanonicalSMILES",
    "IsomericSMILES",
    "InChI",
    "InChIKey",
    "IUPACName",
    "XLogP",
    "TPSA",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "RotatableBondCount",
]


class PubChemAdapter(SourceAdapter):
    name = "PubChem"
    provides = (CATEGORY_IDENTITY, CATEGORY_PHYSCHEM)

    def __init__(self, timeout: int = 10, session: Optional[requests.Session] = None):
        self.timeout = timeout
        self.session = session or requests

    def fetch(self, drug_name=None, smiles=None, categories=None) -> SourceResult:
        if not drug_name and not smiles:
            return self._not_found("no drug_name or smiles provided")

        if drug_name:
            url = f"{_BASE}/compound/name/{requests.utils.quote(str(drug_name))}/property/{','.join(_PROPS)}/JSON"
        else:
            url = f"{_BASE}/compound/smiles/{requests.utils.quote(str(smiles))}/property/{','.join(_PROPS)}/JSON"

        try:
            resp = self.session.get(url, timeout=self.timeout)
        except Exception as exc:  # network failure — degrade, don't crash
            return self._error(str(exc))

        if resp.status_code == 404:
            return self._not_found()
        if resp.status_code != 200:
            return self._error(f"HTTP {resp.status_code}")

        try:
            props = resp.json()["PropertyTable"]["Properties"][0]
        except (KeyError, IndexError, ValueError) as exc:
            return self._error(f"unexpected payload: {exc}")

        cid = props.get("CID")
        ref = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else None
        result = self._ok()

        def prov() -> Provenance:
            return Provenance(source=self.name, reference=ref)

        # -- identity (all RECORDED) ------------------------------------------
        identity = {
            "pubchem_cid": props.get("CID"),
            "iupac_name": props.get("IUPACName"),
            "molecular_formula": props.get("MolecularFormula"),
            "smiles": props.get("IsomericSMILES") or props.get("CanonicalSMILES"),
            "inchi": props.get("InChI"),
            "inchikey": props.get("InChIKey"),
        }
        for fname, val in identity.items():
            if val is not None:
                result.add_field(CATEGORY_IDENTITY, fname, FieldValue(val, None, Evidence.RECORDED, prov()))

        # -- physicochemical --------------------------------------------------
        # (field, unit, evidence)
        phys = [
            ("molecular_weight", props.get("MolecularWeight"), "g/mol", Evidence.RECORDED),
            ("xlogp", props.get("XLogP"), None, Evidence.PREDICTED),
            ("tpsa", props.get("TPSA"), "Å²", Evidence.PREDICTED),
            ("hbd", props.get("HBondDonorCount"), None, Evidence.RECORDED),
            ("hba", props.get("HBondAcceptorCount"), None, Evidence.RECORDED),
            ("rotatable_bonds", props.get("RotatableBondCount"), None, Evidence.RECORDED),
        ]
        for fname, val, unit, ev in phys:
            if val is not None:
                result.add_field(CATEGORY_PHYSCHEM, fname, FieldValue(_num(val), unit, ev, prov()))

        return result


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v
