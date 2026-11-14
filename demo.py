"""Small illustrative numerical scenario; not a reproduction of paper tables."""
from __future__ import annotations
import argparse,json,csv,math
from pathlib import Path
import numpy as np
from .aac_hocbf import AACController,ControllerState,Config,TargetMessage


def run_demo(output: str, duration: float=12.0, backend: str='scipy_slsqp'):
    c=Config(solver=backend,slack_weight=1e4 if backend=='scipy_slsqp' else 1e6)
    ctrl=AACController(c)
    p0=np.array([[-6.0,-3.0],[6.0,3.0]])
    state=ControllerState(p0,np.zeros_like(p0))
    pt=np.array([[4.0,3.5],[-4.0,-3.5]])
    target_vel=np.array([[0.04,0.0],[-0.04,0.0]])
    # target message stamped at t=0 in the illustrative example; refreshed
    # every 0.5 s. No packet loss or realistically delayed network here.
    latest=[TargetMessage(pt[i].copy(),target_vel[i].copy(),0.) for i in range(2)]
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    trajectory=[];solver_failures=0;active=0;released_at=None
    steps=int(duration/c.dt)
    for k in range(steps+1):
        now=round(k*c.dt,9)
        if k % 5==0:
            latest=[TargetMessage(pt[i]+now*target_vel[i],target_vel[i],now) for i in range(2)]
        dist=float(np.linalg.norm(state.positions[0]-state.positions[1]))
        row={'step':k,'time_s':now,'phase':state.phase,'separation_m':dist,
             'uav1_x':state.positions[0,0],'uav1_y':state.positions[0,1],
             'uav2_x':state.positions[1,0],'uav2_y':state.positions[1,1],
             'uav1_vx':state.velocities[0,0],'uav1_vy':state.velocities[0,1],
             'uav2_vx':state.velocities[1,0],'uav2_vy':state.velocities[1,1]}
        if k<steps:
            state,diag=ctrl.step(now,state,latest)
            row.update({'solver_ok':int(diag['success']),'cbf_active':int(diag['active']),
                        'max_slack':diag['max_slack'],'max_aoi_s':diag['age_max']})
            solver_failures+=int(not diag['success']);active+=int(diag['active'])
            if released_at is None and diag['released']:released_at=now
        trajectory.append(row)
    with (out/'demo_trajectory.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=trajectory[0].keys());w.writeheader();w.writerows(trajectory)
    report={'kind':'illustrative independent reference run, NOT original manuscript experiment',
            'backend':backend,'duration_s':duration,'steps':steps,'release_time_s':released_at,
            'min_sampled_separation_m':float(min(r['separation_m'] for r in trajectory)),
            'solver_failures':solver_failures,'active_steps':active,
            'safety_guarantee':'none; sampled numerical illustration only'}
    (out/'demo_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_runs')
    p.add_argument('--duration',type=float,default=12.0)
    p.add_argument('--backend',choices=['scipy_slsqp','cvxpy_ecos'],default='scipy_slsqp')
    a=p.parse_args();run_demo(a.output,a.duration,a.backend)
