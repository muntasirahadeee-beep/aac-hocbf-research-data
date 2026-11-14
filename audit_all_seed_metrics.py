#!/usr/bin/env python3
"""Audit synchronization flags in saved per-seed CSVs against ATD<=0.5 s.

The output is *newly derived audit data*, NOT repaired original simulations.
"""
import argparse,csv,collections,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'
INPUTS=[
('Temporal (Table 6)','tro_v8_event_release/v8_independent_seed_metrics.csv',['method']),
('Kinematic baseline (Table 7)','tro_v8_gazebo_validation_1101_1110/gazebo_validation_seed_metrics.csv',['method']),
('Kinematic safety (Table 7)','tro_v8_gazebo_hocbf_1101_1110/hocbf_all_method_seed_metrics.csv',['method']),
('Ablations (Table 8)','tro_v8_five_uav_ablation/ablation_seed_metrics.csv',['method']),
('Network (Table 9)','tro_v8_network_severity/network_severity_seed_metrics.csv',['condition']),
('Scalability (Table 10)','tro_v8_scalability_3_5_8_10/scalability_seed_metrics.csv',['uav_count','method']),
]

def boolean(val):
    try: return int(float(val)) == 1
    except(ValueError,TypeError):return False

def number(val):
    try: return float(val)
    except(ValueError,TypeError):return float('nan')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--strict',action='store_true',help='Return exit status 1 if mismatches found');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    groups=collections.defaultdict(list); mismatches=[]; details=[]
    for study,rel,keyfields in INPUTS:
        with (ROOT/'data'/rel).open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        for row in rows:
            key='|'.join(row.get(k,'') for k in keyfields)
            present=boolean(row.get('all_arrived'))
            a=number(row.get('arrival_difference_s'))
            flag=boolean(row.get('synchronization_success'))
            # The manuscript defines <=0.5. Tiny tolerance is for float conversion, not threshold redesign.
            computed=present and math.isfinite(a) and a<=0.5+1e-9
            groups[(study,key,rel)].append((flag,computed))
            if flag!=computed:
                mismatches.append({'study':study,'group':key,'seed':row.get('seed',row.get('random_seed','')),'stored_sync_flag':int(flag),'computed_from_ATD':int(computed),'all_arrived':int(present),'arrival_difference_s':row.get('arrival_difference_s',''),'original_file':f'data/{rel}'})
    for (study,key,rel),xs in sorted(groups.items()):
        details.append({'study':study,'group':key,'n':len(xs),'stored_flag_success':sum(p[0] for p in xs),'ATD_threshold_success':sum(p[1] for p in xs),'flag_mismatch_rows':sum(p[0]!=p[1] for p in xs),'original_file':f'data/{rel}'})
    for fname,items in [('SYNC_FLAG_MISMATCHES.csv',mismatches),('SEED_METRICS_AUDIT.csv',details)]:
        path=OUT/fname
        if not items: continue
        with path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=items[0].keys());writer.writeheader();writer.writerows(items)
    print('GROUP COUNTS — stored flags vs recalculated 0.5-s synchronization threshold')
    for d in details:
        print(f"{d['study']:30} {d['group']:24} n={d['n']:3}  flag={d['stored_flag_success']:3}  ATD={d['ATD_threshold_success']:3} mismatch_rows={d['flag_mismatch_rows']}")
    print(f"TOTAL: {len(mismatches)} mismatched records. See reports/SYNC_FLAG_MISMATCHES.csv")
    if args.strict and mismatches:return 1
    return 0
if __name__=='__main__':sys.exit(main())
