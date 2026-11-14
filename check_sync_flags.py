#!/usr/bin/env python3
"""Post-hoc synchronization consistency check. Does NOT run the UAV controller or Gazebo."""
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]
THRESHOLD=0.5

def read(path):
    with (ROOT/path).open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def check(rel,methodcol,groupcols):
    rows=read(rel)
    print(f"\n{rel} ({len(rows)} rows)")
    groups={}
    for row in rows:
        key=tuple(row[c] for c in groupcols)
        groups.setdefault(key,[]).append(row)
    for key,items in sorted(groups.items()):
        flag=sum(int(float(x.get('synchronization_success') or 0)) for x in items)
        calc=0
        offending=[]
        for x in items:
            atd=x.get('arrival_difference_s','')
            try: a=float(atd)
            except (ValueError,TypeError):continue
            if int(float(x.get('all_arrived') or 0))==1 and a<=THRESHOLD:
                calc+=1
            if int(float(x.get('synchronization_success') or 0))==1 and a>THRESHOLD:
                offending.append((x.get('seed','?'),a))
        print(f"  {'/'.join(key):18} flags={flag}/{len(items)}  ATD<=0.5={calc}/{len(items)}")
        if offending:print('     flagged-success but ATD>0.5:',offending)

if __name__=='__main__':
    check(Path('data/tro_v8_event_release/v8_independent_seed_metrics.csv'),'method',['method'])
    check(Path('data/tro_v8_gazebo_validation_1101_1110/gazebo_validation_seed_metrics.csv'),'method',['method'])
