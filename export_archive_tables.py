#!/usr/bin/env python3
"""Export paper-aligned *archived summary* values; does not rerun the simulations."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=ROOT/'reports'/'ARCHIVED_PAPER_TABLES.csv'
TABLES=[
    ('Table 6 - temporal benchmark','tro_v8_event_release/v8_independent_method_summary.csv', ['method','arrival_rate_percent','sync_success_percent','atd_mean_s','atd_p95_s','atd_max_s','completion_mean_s']),
    ('Table 7 - Gazebo HOCBF comparison','tro_v8_gazebo_hocbf_1101_1110/hocbf_all_method_summary.csv', ['method','arrival_rate_percent','sync_success_percent','atd_p95_successful_s','minimum_separation_m','minimum_clearance_m','mean_filter_activation_percent','mean_completion_successful_s']),
    ('Table 8 - ablations','tro_v8_five_uav_ablation/ablation_method_summary.csv', ['variant','arrival_rate_percent','sync_rate_percent','safety_rate_percent','atd_p95_s','minimum_separation_min_m','braking_violation_mean','completion_mean_s']),
    ('Table 9 - communication severity','tro_v8_network_severity/network_severity_summary.csv', ['condition','arrival_rate_percent','sync_rate_percent','safety_rate_percent','atd_p95_s','maximum_message_age_p95_s','completion_p95_s','minimum_separation_min_m']),
    ('Table 10 - scaling','tro_v8_scalability_3_5_8_10/scalability_method_summary.csv', ['uav_count','method','arrival_rate_percent','sync_rate_percent','safety_rate_percent','atd_p95_s','minimum_separation_p05_m','serial_p95_control_step_ms']),
]

def main():
    OUT.parent.mkdir(exist_ok=True)
    allrows=[]
    for paper,path,fields in TABLES:
        with (DATA/path).open(newline='',encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        for r in rows:
            for field in fields:
                if field not in r: raise KeyError(f"{field} missing from {path}")
                allrows.append({'table':paper,'method_or_variant':r.get('method') or r.get('variant') or r.get('condition'),'team_size':r.get('uav_count',''),'field':field,'archived_value':r[field],'source_file':f'data/{path}'})
    with OUT.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['table','method_or_variant','team_size','field','archived_value','source_file']);writer.writeheader();writer.writerows(allrows)
    print(f"Exported {len(allrows)} summary-field records to {OUT.relative_to(ROOT)}")
    print('CAUTION: archival export only, not an independent experiment rerun; compare inconsistencies in docs/AUDIT_FINDINGS.md')
if __name__=='__main__':main()
