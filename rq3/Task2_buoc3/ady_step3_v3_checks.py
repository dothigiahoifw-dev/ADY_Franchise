"""ADY RQ3 Step 3 v3 - reproducible core checks. Inputs: uploads/*.csv + project box_office_detailed.csv. Writes *_v3 files; never overwrites older outputs."""
import pandas as pd, numpy as np
U='/mnt/user-data/uploads/'; O='/mnt/user-data/outputs/step3_v3/'
m=pd.read_csv(U+'analysis_master_transitions.csv',low_memory=False)
det=pd.read_csv('/mnt/project/box_office_detailed.csv').dropna(subset=['opening_weekend_gross'])
# ---- P1 checks
assert m.transition_id.is_unique
y=m[m.Y.notna()].copy()
assert len(y)==918 and (y.open_prev>0).all() and (y.open_curr>0).all()
assert np.allclose(np.log(y.open_curr)-np.log(y.open_prev),y.Y)
assert (y.franchise_position_n>=2).all()
# ---- flags
g=lambda s,c:y[{'dom':f'raw_box_office_detailed__domestic_gross_{s}','glo':f'raw_box_office_raw__global_gross_{s}','op':f'open_{s}'}[c]]
y['f_open_gt_domestic']=(g('prev','op')>g('prev','dom'))|(g('curr','op')>g('curr','dom'))
y['f_open_gt_global']=(g('prev','op')>g('prev','glo'))|(g('curr','op')>g('curr','glo'))   # NaN -> False (missing != violation)
y['f_open_gt_gross_any']=y.f_open_gt_domestic|y.f_open_gt_global
y['f_global_lt_domestic_same_film']=(g('prev','glo')<g('prev','dom'))|(g('curr','glo')<g('curr','dom'))
key=det.groupby(['opening_weekend_gross','domestic_gross'],dropna=False).film_key.transform('size')
dup=set(det[key>1].film_key)
y['f_dup_value_across_films']=y.film_key_prev.isin(dup)|y.film_key_curr.isin(dup)
y['f_Y_exact_zero']=y.Y==0
y['f_small_lt100k_unverified_currency']=(y.open_prev<1e5)|(y.open_curr<1e5)
y['f_small_lt1pct_domestic']=(g('prev','op')/g('prev','dom')<.01)|(g('curr','op')/g('curr','dom')<.01)
y['f_suspect']=y.f_open_gt_gross_any|y.f_dup_value_across_films   # 11 pairs
# ---- samples
S={'A0_ref_all_Y':y.index==y.index,'A1_drop_suspect':~y.f_suspect,
   'A2_drop_suspect_and_lt100k':~(y.f_suspect|y.f_small_lt100k_unverified_currency)}
for k,v in S.items(): y.loc[v,['transition_id']].to_csv(O+f'ids_{k}_v3.csv',index=False)
# ---- B: chains. total valid transitions per franchise (collection order incl. films without opening)
tv=m.groupby('franchise_id').franchise_position_n.agg(['min','max','size']).rename(columns={'size':'n_valid'})
def chains(df,tag):
    out={}
    for fid,s in df.groupby('franchise_id'):
        p=sorted(s.franchise_position_n); 
        # longest contiguous run of positions
        best=cur=1
        for a,b in zip(p,p[1:]): cur=cur+1 if b==a+1 else 1; best=max(best,cur)
        if len(p)==1: best=1
        t=tv.loc[fid]; full=(len(p)==t.n_valid)         # every observed transition has Y
        out[fid]=dict(n_Y=len(p),run=best,from2=(p[0]==2 and best==len(p)),full=full)
    r=pd.DataFrame(out).T; 
    res={f'{tag}_any_run>=3':(r.run>=3).sum(),f'{tag}_run_from_1to2_>=3':((r.run>=3)&(r.from2.astype(bool))).sum(),
         f'{tag}_FULL_chain_>=3':((r.full.astype(bool))&(r.n_Y>=3)).sum(),f'{tag}_FULL_chain_>=4':((r.full.astype(bool))&(r.n_Y>=4)).sum()}
    return res,r
rows=[]
for k in ['A0_ref_all_Y','A1_drop_suspect','A2_drop_suspect_and_lt100k']:
    df=y[S[k]]; res,r=chains(df,k)
    fullids=r[(r.full.astype(bool))&(r.n_Y>=3)].index
    nt=df[df.franchise_id.isin(fullids)]
    res[f'{k}_FULL>=3_transitions']=len(nt); rows.append(res)
    nt[['transition_id','franchise_id','franchise_position_n']].to_csv(O+f'ids_B_full_chain_ge3_on_{k}_v3.csv',index=False)
    print(k,res)
# ---- audit table for suspicious pairs
cols=['transition_id','franchise_id','title_prev','title_curr','release_date_prev','release_date_curr','open_prev','open_curr','Y',
 'raw_box_office_detailed__domestic_gross_prev','raw_box_office_raw__global_gross_prev','raw_box_office_detailed__domestic_gross_curr','raw_box_office_raw__global_gross_curr',
 'f_open_gt_domestic','f_open_gt_global','f_global_lt_domestic_same_film','f_dup_value_across_films','f_Y_exact_zero']
y[y.f_suspect][cols].to_csv(O+'audit_suspect_pairs_v3.csv',index=False)
# ---- A table (point estimates only; no bootstrap rerun)
y['pos']=np.where(y.franchise_position_n>=6,'>=6',y.franchise_position_n.astype(str))
for k,v in S.items():
    d=y[v]; t=d.groupby('pos').agg(n=('Y','size'),franchises=('franchise_id','nunique'),med_pct=('Y',lambda s:100*(np.exp(s.median())-1)),share_Y_lt0=('Y',lambda s:(s<0).mean()))
    print(k,len(d),d.franchise_id.nunique());print(t.round(3))
# ---- filter table
base=y; seq=[('Y exists (ref)',base)]
print(y[['f_open_gt_domestic','f_open_gt_global','f_dup_value_across_films','f_global_lt_domestic_same_film','f_small_lt100k_unverified_currency','f_small_lt1pct_domestic','f_Y_exact_zero']].sum())
y.to_pickle('/tmp/y.pkl')
