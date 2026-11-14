#!/usr/bin/env python3
"""ADY_PRJ: loss-aware, reusable analysis master over DP v3.3.

Usage (from project root):
    py scripts\\build_analysis_master.py --base-dir .

Requires v3.3's output files and the same five original raw CSVs in data/raw/.
Never changes v3.3 outputs, raw files, or the project's fixed opening Y.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

RAW_FILES = {
    'movies': 'movies_raw.csv',
    'box_office_raw': 'box_office_raw.csv',
    'box_office_detailed': 'box_office_detailed.csv',
    'rt_scores': 'rt_scores.csv',
    'credits': 'credits_raw.csv',
}
SINGLE_FILM = ['movies', 'box_office_raw', 'box_office_detailed', 'rt_scores']
MAIN_OUTCOMES = {
    'Y': 'Opening-weekend log change; fixed primary target; comparability assumed',
    'Y_lifetime_global': 'Global lifetime gross log change; TMDB source; NOT opening',
    'Y_lifetime_domestic': 'Domestic lifetime gross log change; detailed source; NOT opening',
    'Y_lifetime_international': 'International lifetime gross log change; detailed source; NOT opening',
    'delta_critic_score_snapshot': 'Difference in observed critic scores; 2026 snapshot',
    'delta_audience_score_snapshot': 'Difference in observed audience scores; 2026 snapshot',
    'budget_log_ratio': 'Production-budget log change when both budgets positive',
    'vote_count_log_change_snapshot': 'Log vote-count change, 2026 snapshot; NOT pre-release',
    'domestic_share_change_detailed': 'Change in domestic share of domestic+international reported totals',
}


def load_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f'Missing required file: {path}')
    return pd.read_csv(path, dtype='string', low_memory=False)


def save_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding='utf-8-sig', na_rep='')


def filehash(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as fin:
        for chunk in iter(lambda: fin.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def num(s):
    return pd.to_numeric(s, errors='coerce').astype('float64')


def finite(x):
    return np.isfinite(x)


def distinct_join_ids(series):
    return '|'.join(dict.fromkeys(str(x) for x in series.dropna() if str(x).strip()))


def assemble_credits(credits):
    if credits['film_key'].isna().any() or credits['film_key'].eq('').any():
        raise ValueError('Missing film_key in credits: cannot reliably attach rows')
    roles = credits['role'].fillna('unknown').str.lower().str.strip()
    credits = credits.assign(_role=roles)
    counts = credits.groupby('film_key', sort=False).agg(
        credits__rows=('person_id', 'size'),
        credits__unique_people=('person_id', 'nunique'),
        credits__roles=('role', distinct_join_ids),
        credits__source_values=('source', distinct_join_ids),
        credits__retrieval_dates=('retrieval_date', distinct_join_ids),
    ).reset_index()
    directors = credits.loc[credits['_role'].str.contains('direct', case=False, na=False)]
    actor_mask = credits['_role'].str.contains('cast|actor|actress|perform', case=False, na=False)
    cast = credits.loc[actor_mask]
    for subset, prefix in [(directors, 'directors'), (cast, 'cast')]:
        by = subset.groupby('film_key', sort=False)['person_id'].agg(distinct_join_ids)
        counts[f'credits__{prefix}_person_ids'] = counts['film_key'].map(by)
        counts[f'credits__{prefix}_unique_people'] = counts[f'credits__{prefix}_person_ids'].map(
            lambda x: len(x.split('|')) if isinstance(x, str) and x else 0)
    orders = pd.to_numeric(credits['billing_order'], errors='coerce')
    credits['_billing_numeric'] = orders
    billed = credits.groupby('film_key', sort=False)['_billing_numeric'].count()
    counts['credits__billing_order_nonmissing'] = counts['film_key'].map(billed).fillna(0).astype('int64')
    return counts


def build_films(raw, labels):
    film = raw['movies'].copy()
    if film['film_key'].isna().any() or film['film_key'].duplicated().any():
        raise ValueError('movies_raw film_key missing/duplicated')
    film = film.rename(columns={c: f'raw_movies__{c}' for c in film.columns if c != 'film_key'})
    audit = []
    for src in SINGLE_FILM[1:]:
        table = raw[src]
        if table['film_key'].isna().any() or table['film_key'].duplicated().any():
            raise ValueError(f'{src} film_key missing/duplicated')
        orphan = int((~table['film_key'].isin(film['film_key'])).sum())
        if orphan:
            raise ValueError(f'{src}: {orphan} orphan film keys')
        renamed = table.rename(columns={c: f'raw_{src}__{c}' for c in table.columns if c != 'film_key'})
        film = film.merge(renamed, how='left', on='film_key', validate='one_to_one')
        audit.append({'source': src, 'source_rows': len(table), 'orphan_film_keys': 0})
    cred = assemble_credits(raw['credits'])
    orphan_credit = int((~cred['film_key'].isin(film['film_key'])).sum())
    if orphan_credit:
        raise ValueError(f'credits: {orphan_credit} orphan film keys')
    film = film.merge(cred, how='left', on='film_key', validate='one_to_one')
    if labels['film_key'].isna().any() or labels['film_key'].duplicated().any():
        raise ValueError('film relationship labels not unique')
    label_cols = [c for c in labels.columns if c != 'film_key' and c not in ('tmdb_collection_id', 'title', 'release_date_ref')]
    film = film.merge(labels[['film_key'] + label_cols], on='film_key', how='left', validate='one_to_one')
    dt = pd.to_datetime(film['raw_movies__release_date_ref'], errors='coerce')
    film['derived__release_year'] = dt.dt.year.astype('Int64')
    film['derived__release_month_from_date'] = dt.dt.month.astype('Int64')
    film['derived__release_decade'] = ((dt.dt.year // 10) * 10).astype('Int64')
    film['derived__collection_id'] = film['raw_movies__tmdb_collection_id']
    film['derived__has_opening'] = num(film['raw_box_office_detailed__opening_weekend_gross']).gt(0)
    for name, src, col in [
        ('lifetime_global', 'box_office_raw', 'global_gross'),
        ('lifetime_domestic', 'box_office_detailed', 'domestic_gross'),
        ('lifetime_international', 'box_office_detailed', 'international_gross'),
        ('critic_score', 'rt_scores', 'critic_score'),
        ('audience_score', 'rt_scores', 'audience_score'),
        ('production_budget', 'movies', 'production_budget'),
    ]:
        arr = num(film[f'raw_{src}__{col}'])
        film[f'derived__has_{name}'] = arr.notna() & finite(arr) & (arr.gt(0) if name in ('lifetime_global','lifetime_domestic','lifetime_international','production_budget') else True)
    # This value is NOT necessarily TMDB global lifetime gross (different provider and coverage).
    dom = num(film['raw_box_office_detailed__domestic_gross'])
    intl = num(film['raw_box_office_detailed__international_gross'])
    denom = dom + intl
    valid = (dom >= 0) & (intl >= 0) & (denom > 0) & finite(denom)
    film['derived__domestic_share_of_detailed_total'] = (dom / denom).where(valid)
    return film, pd.DataFrame(audit)


def add_source_columns(pairs, films):
    """Preserve original attributes on BOTH sides with source-qualified prefixes."""
    if pairs['film_key_prev'].isna().any() or pairs['film_key_curr'].isna().any():
        raise ValueError('Missing pair IDs')
    lookup = films.set_index('film_key')
    cols = list(lookup.columns)
    additions = {}
    for side in ('prev', 'curr'):
        keys = pairs[f'film_key_{side}']
        for c in cols:
            new_name = f'{c}_{side}'
            if new_name not in pairs.columns:
                additions[new_name] = keys.map(lookup[c]).reset_index(drop=True)
    if not additions:
        return pairs.copy()
    # concat once, avoids fragmentation and preserves exact index alignment
    return pd.concat([pairs.reset_index(drop=True), pd.DataFrame(additions)], axis=1)


def add_pair_outcomes(df):
    d = df.copy()
    for name in ('critic_score', 'audience_score'):
        # These are retrospective 2026 snapshot observations (not opening-era scores).
        prev = num(d[f'raw_rt_scores__{name}_prev'])
        curr = num(d[f'raw_rt_scores__{name}_curr'])
        good = prev.between(0, 100) & curr.between(0, 100) & finite(prev) & finite(curr)
        d[f'analysis__delta_{name}_snapshot'] = (curr - prev).where(good)
        d[f'analysis__{name}_both_available'] = good
    prev_votes = num(d['raw_movies__vote_count_prev'])
    curr_votes = num(d['raw_movies__vote_count_curr'])
    valid_votes = (prev_votes > 0) & (curr_votes > 0) & finite(prev_votes) & finite(curr_votes)
    with np.errstate(divide='ignore', invalid='ignore'):
        d['vote_count_log_change_snapshot'] = (np.log(curr_votes.where(valid_votes)) - np.log(prev_votes.where(valid_votes)))
    prev_budget = num(d['raw_movies__production_budget_prev'])
    curr_budget = num(d['raw_movies__production_budget_curr'])
    budget_ok = (prev_budget > 0) & (curr_budget > 0) & finite(prev_budget) & finite(curr_budget)
    d['analysis__budget_abs_change'] = (curr_budget - prev_budget).where(budget_ok)
    d['analysis__budget_pct_change'] = (curr_budget / prev_budget - 1).where(budget_ok)
    prev_share = num(d['derived__domestic_share_of_detailed_total_prev'])
    curr_share = num(d['derived__domestic_share_of_detailed_total_curr'])
    d['domestic_share_change_detailed'] = curr_share - prev_share
    for scope in ('global', 'domestic', 'international'):
        prev = num(d[f'raw_{"box_office_raw" if scope=="global" else "box_office_detailed"}__{"global_gross" if scope=="global" else scope+"_gross"}_prev'])
        curr = num(d[f'raw_{"box_office_raw" if scope=="global" else "box_office_detailed"}__{"global_gross" if scope=="global" else scope+"_gross"}_curr'])
        valid = (prev > 0) & (curr > 0) & finite(prev) & finite(curr)
        with np.errstate(divide='ignore', invalid='ignore'):
            calc = np.log(curr.where(valid)) - np.log(prev.where(valid))
        newc = f'analysis__Y_lifetime_{scope}_recomputed'
        d[newc] = calc
    for c in MAIN_OUTCOMES:
        d[f'analysis__has_{c}'] = d[c].notna() & finite(num(d[c]))
    return d


def inventory_columns(film, master, raw):
    result = []
    for source, df in raw.items():
        for attr in df.columns:
            if attr == 'film_key':
                output = 'film_key'
            elif source == 'credits':
                output = 'credits__* (aggregates); raw credits retains person–film–role rows'
            else:
                output = f'raw_{source}__{attr}'
            result.append({'source_table': source, 'raw_column': attr,
                           'film_master_representation': output,
                           'transition_prev_column': output + '_prev' if source != 'credits' and attr != 'film_key' else ('film_key_prev' if attr == 'film_key' else 'credits__*_prev'),
                           'transition_curr_column': output + '_curr' if source != 'credits' and attr != 'film_key' else ('film_key_curr' if attr == 'film_key' else 'credits__*_curr'),
                           'missing_source_rows': int(df[attr].isna().sum()),
                           'purpose': 'audit/key/source' if attr in ['film_key','source','retrieval_date','rt_url','imdb_id','tmdb_id'] else 'raw attribute; use only with outcome/time caution',
                           'note': 'one-to-many credits; original row-level credits NOT flattened' if source == 'credits' else ''})
    return pd.DataFrame(result)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-dir', default='.', help='Directory containing data/raw/, data/analytical/, reports/')
    args=ap.parse_args(argv)
    base=Path(args.base_dir).resolve()
    out=base/'data/analytical'
    rep=base/'reports'
    rep.mkdir(parents=True, exist_ok=True)
    print('[1/6] Read five raws and v3.3 outputs', flush=True)
    raw={name:load_csv(base/'data/raw'/filename) for name,filename in RAW_FILES.items()}
    diag=load_csv(out/'transitions_diagnostic.csv')
    cand=load_csv(rep/'pairs_audit.csv')
    labels=load_csv(rep/'film_relationship_labels.csv')
    baseline=load_csv(out/'transitions_model_rq1.csv')
    if not diag['transition_id'].is_unique or diag['transition_id'].isna().any():
        raise ValueError('Diagnostic has invalid transition IDs')
    if len(cand) != len(cand[['film_key_prev','film_key_curr']].drop_duplicates()):
        raise ValueError('Candidate pair IDs duplicated')
    print('[2/6] Assemble film-level master (including credit aggregates)',flush=True)
    film, source_audit=build_films(raw,labels)
    print('[3/6] Enrich every technically valid transition with raw attributes for N-1 AND N', flush=True)
    trans=add_source_columns(diag,film)
    trans=add_pair_outcomes(trans)
    print('[4/6] Preserve every candidate; no outcome is fabricated for excluded pairs',flush=True)
    candidate=add_source_columns(cand,film)
    # All valid diagnostics (including derived features) join 1:1 to candidate population.
    # Invalid pairs have unknown/ambiguous adjacency: analytical outcomes left missing.
    extra_cols=[c for c in trans.columns if c not in candidate.columns and c not in ('film_key_prev','film_key_curr')]
    candidate=candidate.merge(trans[['film_key_prev','film_key_curr']+extra_cols],
                              how='left',on=['film_key_prev','film_key_curr'],validate='one_to_one')
    valid_mask=candidate['technically_valid'].str.lower().eq('true')
    if int(valid_mask.sum()) != len(diag):
        raise ValueError('Candidate/valid transition mismatch')
    # Credits must stay at person-film-role grain so original billing_order/person_id is not lost.
    credits_detail=raw['credits'].merge(
        film[['film_key','raw_movies__title','raw_movies__tmdb_collection_id',
              'raw_movies__release_date_ref','relationship_type_candidate']],
        on='film_key', how='left', validate='many_to_one')
    credits_detail=credits_detail.rename(columns={
        'raw_movies__title':'film_title',
        'raw_movies__tmdb_collection_id':'tmdb_collection_id',
        'raw_movies__release_date_ref':'film_release_date'})
    print('[5/6] Validate invariants and write outputs',flush=True)
    checks=[]
    def check(name, condition, observed):
        checks.append({'check':name,'status':'PASS' if bool(condition) else 'FAIL','observed':str(observed)})
    check('film keys unique, no lost films',film['film_key'].is_unique and len(film)==len(raw['movies']),len(film))
    check('credits preserved at original row grain',len(credits_detail)==len(raw['credits']) and
          credits_detail[list(raw['credits'].columns)].equals(raw['credits']),len(credits_detail))
    check('valid transitions match v3.3',len(trans)==len(diag) and trans['transition_id'].equals(diag['transition_id']),len(trans))
    check('all candidates retained',len(candidate)==len(cand),len(candidate))
    check('candidate valid count same as diagnostic',int(valid_mask.sum())==len(diag),int(valid_mask.sum()))
    check('opening Y exactly unchanged',trans['Y'].equals(diag['Y']), int(trans['Y'].notna().sum()))
    check('RQ1 Y rows/values unchanged',
          len(baseline)==int(trans['Y'].notna().sum()) and
          baseline.set_index('transition_id')['Y'].equals(trans.loc[trans['Y'].notna()].set_index('transition_id').loc[baseline['transition_id'],'Y']),
          len(baseline))
    for scope in ('global','domestic','international'):
        a=num(trans[f'Y_lifetime_{scope}']);b=num(trans[f'analysis__Y_lifetime_{scope}_recomputed'])
        check(f'lifetime {scope} log change independently recalculated',np.allclose(a,b,rtol=1e-10,atol=1e-10,equal_nan=True),int(a.notna().sum()))
    for sc in ('critic_score','audience_score'):
        a=num(trans[f'delta_{sc}_snapshot']);b=num(trans[f'analysis__delta_{sc}_snapshot'])
        check(f'{sc} deltas consistent with v3.3',np.allclose(a,b,rtol=1e-10,atol=1e-10,equal_nan=True),int(a.notna().sum()))
    check('candidate valid Y subset equals transitions',
          np.allclose(num(candidate.loc[valid_mask,'Y']),
                      num(candidate.loc[valid_mask].set_index(['film_key_prev','film_key_curr'])
                          .index.map(trans.set_index(['film_key_prev','film_key_curr'])['Y'])), equal_nan=True),
          int(candidate.loc[valid_mask,'Y'].notna().sum()))
    check('film-level relationship labels complete',film['relationship_type_candidate'].notna().all(),len(film))
    check('all raw 41 source columns inventoried',sum(len(x.columns) for x in raw.values())==41, sum(len(x.columns) for x in raw.values()))
    validation=pd.DataFrame(checks)
    save_csv(validation,rep/'analysis_master_validation.csv')
    if validation['status'].eq('FAIL').any():
        raise AssertionError('Master validation failed: '+validation.loc[validation['status'].eq('FAIL'),'check'].str.cat(sep='; '))
    save_csv(film,out/'analysis_master_films.csv')
    save_csv(credits_detail,out/'analysis_credits_detail.csv')
    save_csv(trans,out/'analysis_master_transitions.csv')
    save_csv(candidate,out/'analysis_master_candidates.csv')
    cov=[]
    for name,note in MAIN_OUTCOMES.items():
        available=trans[f'analysis__has_{name}'].astype('boolean').fillna(False)
        cov.append({'outcome':name,'meaning':note,'n_valid_pairs_total':len(trans),
                    'n_pairs_with_outcome':int(available.sum()),
                    'pct_valid_pairs_with_outcome':round(float(available.mean()*100),3),
                    'n_distinct_franchises':int(trans.loc[available,'franchise_id'].nunique()),
                    'n_also_have_opening_Y':int((available & trans['Y'].notna()).sum()),
                    'interpretation':'retrospective only' if 'score' in name or 'vote' in name or 'lifetime' in name else 'see methodology'})
    coverage_df = pd.DataFrame(cov)
    save_csv(coverage_df,rep/'analysis_master_outcome_coverage.csv')
    outcomes_long = []
    keys = ['transition_id','franchise_id','film_key_prev','film_key_curr']
    for outcome, meaning in MAIN_OUTCOMES.items():
        sub = trans.loc[trans[f'analysis__has_{outcome}'].astype('boolean').fillna(False), keys + [outcome]].copy()
        sub = sub.rename(columns={outcome:'outcome_value'})
        sub['outcome_name'] = outcome
        sub['outcome_definition'] = meaning
        sub['primary_project_target'] = outcome == 'Y'
        outcomes_long.append(sub)
    long_df = pd.concat(outcomes_long,ignore_index=True)
    long_df = long_df[keys + ['outcome_name','outcome_value','primary_project_target','outcome_definition']]
    save_csv(long_df,out/'analysis_outcomes_long.csv')
    if len(long_df) != int(coverage_df['n_pairs_with_outcome'].sum()):
        raise ValueError('Long format outcome counts do not match coverage report')
    colinventory=inventory_columns(film,trans,raw)
    save_csv(colinventory,rep/'analysis_master_raw_column_mapping.csv')
    derived=[c for c in trans.columns if not c.startswith('raw_') and not c.startswith('credits__')]
    derived_catalog=[]
    for c in derived:
        derived_catalog.append({'column':c,'nonmissing_valid_pairs':int(trans[c].notna().sum()),
                                'data_role':'primary_outcome' if c=='Y' else ('secondary_outcome' if c in MAIN_OUTCOMES else ('raw_source_or_audit' if c.startswith('film_key') else 'diagnostic_or_identifier')),
                                'rq1_predictor_use':'DO_NOT_USE_DIRECTLY; use separate v3.3 RQ1 baseline' if c!='Y' else 'TARGET_NOT_X',
                                'source_note':MAIN_OUTCOMES.get(c,'Check v3.3 reports and raw_column_mapping; no causal interpretation')})
    save_csv(pd.DataFrame(derived_catalog),rep/'analysis_master_column_catalog.csv')
    manifest={'inputs':{k:{'path':str(base/'data/raw'/v),'rows':len(raw[k]),'sha256':filehash(base/'data/raw'/v)} for k,v in RAW_FILES.items()},
              'outputs':{'analysis_master_films.csv':{'rows':len(film),'columns':len(film.columns)},
                         'analysis_master_transitions.csv':{'rows':len(trans),'columns':len(trans.columns)},
                         'analysis_master_candidates.csv':{'rows':len(candidate),'columns':len(candidate.columns)},
                         'analysis_credits_detail.csv':{'rows':len(credits_detail),'columns':len(credits_detail.columns)},
                         'analysis_outcomes_long.csv':{'rows':len(long_df),'columns':len(long_df.columns)}},
              'coverage':cov,
              'source_columns_inventoried':len(colinventory),
              'validation':{'pass':int(validation['status'].eq('PASS').sum()),'fail':int(validation['status'].eq('FAIL').sum())},
              'fixed_primary_target':'Y=ln(open_N)-ln(open_N-1); unchanged from v3.3',
              'limitations':['All franchise membership based on TMDB collection assumption.',
                             'Opening comparability is assumed, not externally verified.',
                             'Lifetime global and detailed domestic/international come from different raw sources.',
                             'Scores and vote counts are snapshots, cannot be assumed pre-release.',
                             'Title-heuristic relationship labels are not verified film relationships.',
                             'Many outcomes missing; never fill missing outcomes with zeros.',
                             'Raw credits remain person-film-role rows, summarized in film master; no row explosion.',
                             'Technically excluded candidate pairs are preserved for auditing, not valid chronological transitions.']}
    (rep/'analysis_master_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    print('[6/6] Complete. Wrote analysis_master_films / transitions / candidates and coverage reports.',flush=True)
    print(pd.DataFrame(cov)[['outcome','n_pairs_with_outcome','n_distinct_franchises']].to_string(index=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
