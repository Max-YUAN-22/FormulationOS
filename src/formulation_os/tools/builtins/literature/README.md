# Literature (Mock)

A mock implementation of an academic literature search tool.

**Status:** Mock. Returns canned paper entries derived deterministically from the query. Replace with a real PubMed / CrossRef / OpenAlex wrapper when wiring real models.

## When to use

- User asks "what's known about X"
- User wants references / citations
- User wants background for a formulation choice

## Mock behavior

Returns a deterministic list of synthetic paper entries. Same query always yields the same papers. Includes:

- Synthetic titles referencing the query
- Fake but plausible author lists
- A `doi: null` flag on most entries
- `warnings: ["MOCK OUTPUT"]`

## Replacing with a real tool

1. Implement a real backend calling PubMed E-utilities, CrossRef, or OpenAlex.
2. Update `backend.py` or change `executor.type` to `http` and point at a deployed API.
3. Flip `mock: false`.