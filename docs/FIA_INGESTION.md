# FIA decision ingestion

APEX indexes FIA stewards' decisions and technical regulations as RAG chunks
so Granite can cite the actual rules text behind its explanations. The PDFs
themselves are **not** checked into the repo (they're large and the FIA
publishes them at fixed URLs). This document explains the convention.

## Where to put files

```
backend/fia_pdfs/
├── decision_documents/
│   ├── 2021/
│   │   ├── round_22_abu_dhabi.pdf
│   │   └── ...
│   ├── 2022/
│   ├── 2023/
│   └── 2024/
└── regulations/
    ├── 2019/
    ├── 2020/
    └── ...
```

- One folder per season. Round-specific decisions go under `decision_documents/{year}/`.
- Whole-season regulation PDFs go under `regulations/{year}/`.
- The directory tree is already created; only the `*.pdf` files need to be added.
- All `*.pdf` entries are gitignored (see [`.gitignore`](../.gitignore)).

## Mapping a PDF to a race

`fia_parser.py` accepts an optional `--race-id` flag. To map a specific decision
to a specific race, look up the race ID first:

```bash
# Find race IDs
psql -d apex -c "select id, season_year, round, name from races where season_year=2021 and round=22"

# Ingest one decision tied to that race
python -m ingestion.fia_parser backend/fia_pdfs/decision_documents/2021/round_22_abu_dhabi.pdf --race-id 322
```

If you skip `--race-id` the chunks are still indexed but won't filter by
race in [`build_race_context`](../backend/ai/rag.py) — useful for season-wide
regulations.

## Bulk ingest an entire tree

```bash
python -m ingestion.fia_parser backend/fia_pdfs/
```

This walks every `*.pdf` under the directory and indexes each one. Race IDs
are not inferred — every chunk is indexed without a race-specific filter.
For race-specific mapping, run files individually.

## Confirm it worked

```sql
SELECT metadata->>'source' AS source, COUNT(*)
FROM race_embeddings
GROUP BY 1;
```

Expect a `fia_decision` row alongside `race_narrative` once any PDF has been
parsed.

## Where the PDFs come from

- Stewards' decisions: <https://www.fia.com/documents/> (filter by championship + season)
- Technical regulations: <https://www.fia.com/regulation/category/110>

Both are public; we just don't redistribute them in this repo to keep clone
sizes manageable.

## What gets extracted

`fia_parser.py` uses IBM **Docling** as the primary extractor, with
`pypdfium2` as a fallback when Docling isn't installed or fails on a
particular file. Each PDF becomes a `markdown` blob, then `ai.rag.chunk_text`
splits it into 800-character chunks with 120-character overlap before they
land in `race_embeddings` as `fia_decision`-tagged rows.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `(Docling not installed...)` in output | Docling missing | `pip install docling` |
| `(Docling failed on X: ...)` | Encrypted PDF | Re-export from a PDF viewer, then re-run |
| No `fia_decision` rows after ingest | RAG embedding worker hit watsonx error | Re-run; chunks are upserted, not duplicated |
