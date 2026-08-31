"""Tests for the Orange Book adapter (local DB, no network)."""

from __future__ import annotations

import sqlite3

from formulation_os.knowledge.sources.orange_book import OrangeBookAdapter
from formulation_os.knowledge.sources.schema import (
    CATEGORY_APPROVED,
    CATEGORY_PATENTS,
    SourceStatus,
)


def _make_ob_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE products (ingredient TEXT, df_route TEXT, trade_name TEXT,
            applicant TEXT, strength TEXT, appl_type TEXT, appl_no TEXT,
            product_no TEXT, te_code TEXT, approval_date TEXT, rld TEXT, rs TEXT,
            type TEXT, applicant_full_name TEXT);
        CREATE TABLE patents (appl_type TEXT, appl_no TEXT, product_no TEXT,
            patent_no TEXT, patent_expire_date TEXT, drug_substance_flag TEXT,
            drug_product_flag TEXT, patent_use_code TEXT, delist_flag TEXT,
            submission_date TEXT);
        CREATE TABLE exclusivity (appl_type TEXT, appl_no TEXT, product_no TEXT,
            exclusivity_code TEXT, exclusivity_date TEXT);
        """
    )
    conn.execute(
        "INSERT INTO products VALUES ('CELECOXIB','CAPSULE;ORAL','CELEBREX','PFIZER',"
        "'200MG','N','020998','001','AB','Dec 31, 1998','Yes','Yes','RX','Pfizer Inc')"
    )
    conn.execute(
        "INSERT INTO patents VALUES ('N','020998','001','5760068','Jun 14, 2015','Y','N','U-xxx','N','Aug 1, 2003')"
    )
    conn.execute(
        "INSERT INTO exclusivity VALUES ('N','020998','001','NCE','Dec 31, 2003')"
    )
    conn.commit()
    conn.close()


def test_orange_book_returns_patents_and_exclusivity_separately(tmp_path):
    db = tmp_path / "ob.db"
    _make_ob_db(str(db))
    res = OrangeBookAdapter(db_path=str(db)).fetch(drug_name="Celecoxib")

    assert res.status == SourceStatus.OK
    patents = res.records[CATEGORY_PATENTS]
    types = {r["type"].value for r in patents}
    assert types == {"patent", "regulatory_exclusivity"}

    pat = next(r for r in patents if r["type"].value == "patent")
    exc = next(r for r in patents if r["type"].value == "regulatory_exclusivity")
    assert pat["patent_number"].value == "5760068"
    assert pat["patent_expire_date"].value == "Jun 14, 2015"
    assert exc["exclusivity_expiration_date"].value == "Dec 31, 2003"
    # patent has no exclusivity fields and vice versa (kept separate)
    assert "exclusivity_code" not in pat
    assert "patent_number" not in exc

    # products carry RLD / reference standard / application+product number
    prods = res.records[CATEGORY_APPROVED]
    assert prods[0]["reference_listed_drug"].value == "Yes"
    assert prods[0]["application_number"].value == "N020998"
    assert prods[0]["product_number"].value == "001"


def test_orange_book_unavailable_without_db():
    res = OrangeBookAdapter(db_path="/nonexistent/ob.db").fetch(drug_name="Celecoxib")
    assert res.status == SourceStatus.SOURCE_UNAVAILABLE


def test_orange_book_no_record_for_unknown_drug(tmp_path):
    db = tmp_path / "ob.db"
    _make_ob_db(str(db))
    res = OrangeBookAdapter(db_path=str(db)).fetch(drug_name="Nonexistol")
    assert res.status == SourceStatus.NOT_FOUND
