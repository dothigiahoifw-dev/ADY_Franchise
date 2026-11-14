# ADY201m — DP v3.3: Relationship-type candidates and attribute utilization

**Basis:** The five raw CSVs supplied in this conversation; `complete_dp_pipeline_v3_3.py` executed on the real inputs. All counts below were recomputed in this run. This report does not claim official franchise/narrative relationships, opening-market comparability, causal effects, or modeling performance.

## Project definitions preserved

- Unit: N−1 → N successive releases in the same TMDB collection, ordered by release date (operational franchise assumption).
- Main target: **Y = ln(open_N) − ln(open_N−1)** from `box_office_detailed.opening_weekend_gross`.
- **No substitution of lifetime global/domestic/international gross for opening gross.** The three lifetime changes remain supplementary outcomes only.
- No manual review is required under the team's operational assumption. Source-level missingness/chronology checks remain active.

## Verified processing results

| Metric | Real-data result |
|---|---:|
| Raw film records | 39,871 |
| Candidate pairs | 30,113 |
| Technically valid chronological transitions | 25,943 |
| Transitions with usable opening Y | 918 |
| TMDB collections with usable Y | 562 |
| Film-level relationship annotations (unique `film_key`) | 39,871 |
| Raw source attributes inventoried | 41 / 41 |
| Diagnostic dataset dimensions | 25,943 × 96 |
| Automated checks | 27 PASS; 1 INFO; 0 FAIL |

Independent rechecks: RQ1 baseline and core transitions files are byte-for-byte identical to those shipped in v3.2; Y recomputed from the original opening CSV; label join validated; synthetic title cases for numbered installments and tied dates passed.

## `relationship_type_n` — HEURISTIC CANDIDATES, not verified labels

Source evidence is limited to film **title, TMDB collection, and release-date ordering**. The five raws do NOT have an authoritative `relationship_type` field. Therefore these labels are `UNVERIFIED_TITLE_HEURISTIC`, never officially confirmed movie types.

- Explicit keyword in title (e.g., `Spin-Off`, `Prequel`, `Reboot`, `Remake`, `Sequel`) → corresponding `*_candidate` label. This is a **title clue**, not independent verification.
- A numeric `Part`, `Chapter`, `Vol`, or trailing number with a matching earlier franchise-title root → `sequel_candidate`. This indicates a likely numbered follow-up, but cannot establish narrative continuity.
- Numbered `Episode` (e.g., *Star Wars Episode II*) → `numbered_installment_unknown_type` because numbering may be story order rather than release-order sequel status.
- Reused exact title → `repeated_title_unknown_type` (does not prove remake/reboot).
- Insufficient signals → `unclassified`. The earliest film in a collection is `first_observed_in_collection`, NOT proven to be the original.

Final distribution for the **current film N** of valid transitions:

| Candidate label for N | Valid transitions | With main opening Y |
|---|---:|---:|
| sequel_candidate | 8,193 | 312 |
| prequel_candidate | 5 | 1 |
| spinoff_candidate | 4 | 0 |
| reboot_candidate | 3 | 0 |
| numbered_installment_unknown_type | 577 | 34 |
| repeated_title_unknown_type | 89 | 4 |
| unclassified | 17,072 | 567 |
| **Total** | **25,943** | **918** |

**Interpretation:** Do NOT report "sequel/prequel/spin-off/reboot have different opening trends" from this table. In the opening-Y subset there are no spin-off or reboot candidates and only one prequel candidate. Even `sequel_candidate` is title-heuristic selection, not verified sequel membership. Useful for exploratory stratification and checking title patterns, **not a defensible categorical explanation of performance at this stage**.

## Are all available raw attributes utilized?

**All 41 source columns are inventoried and assigned a role, but NOT all should become model predictors.** Four main groups:

1. **Primary project workflow:** film_key, TMDB collection ID, release date, opening-weekend gross, director/cast credits, previous opening and release timing.
2. **Additional diagnostics now available:** title-number relationship clues, genre overlap, production-company overlap, director-ID overlap, lead-cast superset overlap, top-five cast retention, company/director change, budget change, critic/audience scores, vote count (post-release snapshot), total global/domestic/international gross changes, RT URL match-presence and source missingness flags.
3. **Quality/join provenance, not predictors:** TMDB/IMDb/person/company identifiers, provenance/source, retrieval dates, box-office market_scope, missing_flag, RT matching URL/status, raw release-month consistency, data snapshot fields.
4. **Unavailable in source:** theater_count has zero populated values. Film type (true sequel vs prequel vs reboot) is **not a source attribute** and cannot be reconstructed reliably from title alone. Opening-market/currency/window labels are not supplied.

Coverage among the 918 valid opening-Y transitions:

| Derived attribute | Nonmissing pairs with Y | Recommended use |
|---|---:|---|
| `director_jaccard_snapshot` | 918 | RQ2, possible after timing verification |
| `lead_cast_ids_superset_jaccard_snapshot` | 918 | RQ2, possible after timing verification |
| `genre_jaccard` | 918 | RQ2, possible after timing verification |
| `production_company_jaccard` | 900 | RQ2, possible after timing verification |
| `cast_retention_top5` | 915 | RQ2; pre-release billing availability uncertain |
| `budget_log_ratio` | 743 | RQ2; ~high missingness overall and timing unclear |
| `critic_score_curr` | 841 | RQ2 retrospective only; post-release leakage for RQ1 |
| `audience_score_curr` | 882 | RQ2 retrospective only; post-release leakage for RQ1 |
| `Y_lifetime_global` | 838 | Supplementary lifetime-gross outcome, NOT opening |
| `Y_lifetime_domestic` | 918 | Supplementary lifetime-gross outcome, NOT opening |
| `Y_lifetime_international` | 688 | Supplementary lifetime-gross outcome, NOT opening |
| `relationship_type_n` | 918 | Title-heuristic exploratory category only |

Note that high availability **does not establish validity or predictive relevance**. RT scores and vote counts are 2026 snapshots. The primary 5-feature RQ1 baseline does not include post-release outcomes or relationship title labels.

## Main output files

- `data/analytical/transitions_model_rq1.csv` — **unchanged** 918-row RQ1 baseline, 5 predictors.
- `data/analytical/transitions_model_rq1_relationship_EXPLORATORY.csv` — optional 918-row comparison with unverified title-derived `relationship_type_n`; **NOT the official baseline**.
- `data/analytical/transitions_diagnostic.csv` — 25,943 transitions, now 96 columns, for descriptive/diagnostic study.
- `reports/film_relationship_labels.csv` — film-level label, evidence and verification status (39,871 films).
- `reports/relationship_type_summary.csv` — coverage by label in transition set.
- `reports/diagnostic_feature_coverage.csv` — how many transitions with/without opening Y have each diagnostic attribute.
- `reports/raw_attribute_inventory.csv` — all 41 source attributes with roles.
- `reports/pipeline_validation.csv` — 28 checks, including the informational external-candidate comparison.

## Key limitations and next steps

1. **Operational franchise assumption:** TMDB collection may not encompass every intended franchise branch or may include unusual items.
2. **Opening comparability:** market, currency and opening window unverified, even though the team chose to use existing numeric values.
3. **Title-label coverage:** approximately two-thirds of technically valid transitions have no classified narrative subtype. Manual fact-checking, structured sequel metadata, or other evidence would be needed to claim true relationship types; this project run does not require manual review and therefore does not assert such claims.
4. **Selection:** only 918/25,943 technical pairs have opening Y. Group-based evaluation is required (562 collections represented among those 918).
5. **Do not blindly feed all 96 diagnostic columns into the RQ1 model:** current-film scores, lifetime gross, current-film box-office, and snapshot attributes can leak. Use the separate RQ1 baseline; evaluate exploratory relationships only as an auxiliary experiment.

### How to reproduce

Place `complete_dp_pipeline_v3_3.py` and `build_ady_tables.py` in the same folder. Put the five original raw files under `data/raw/` using the expected names. Run:

```bash
python complete_dp_pipeline_v3_3.py --base-dir /path/to/project --candidate-pairs /path/to/candidate_pairs_full.csv
```

`--candidate-pairs` is optional: without it, the script recreates candidates directly from the same collection/date logic. The 5 raw files are not repackaged here because they have already been supplied by the team.
