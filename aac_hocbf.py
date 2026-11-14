"""Illustrative numerical implementation of AAC + pairwise HOCBF filtering.

PROVENANCE: independently authored in November 2026 from manuscript equations.
NOT the original experiment-generating controller; NO published results recreated.
Planar numerical model only, assumes instantaneous shared UAV state and
known last received target messages. No physical multirotor safety certificate.

Dependencies: numpy and scipy. Optional CVXPY + ECOS backend is available
but is NOT needed for the short standalone demonstration.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import math
import numpy as np
from scipy.optimize import minimize


def saturate(x: np.ndarray, limit: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    mag = float(np.linalg.norm(x))
    return x if mag <= limit else x * (limit / mag)


# Monotonic age-dependent radii as reported in the manuscript, used here for
# an illustrative release calculation. They are NOT recalibrated in this code.
AGE_BINS = ((0.25, .10), (.50, .18), (.75, .30), (1.0, .44),
            (1.25, .62), (1.5, .80), (2.0, 1.12), (2.5, 1.48),
            (3.0, 1.86), (4.0, 2.35), (5.0, 2.95),
            (7.5, 4.40), (11.0, 6.25))


def uncertainty_radius(age: float) -> float:
    if age < 0 or age > 11.0:
        raise ValueError('Age outside calibrated [0, 11] s range')
    for upper, radius in AGE_BINS:
        if age < upper or (upper == 11.0 and age <= upper):
            return radius
    raise AssertionError('Unreachable uncertainty lookup')


def travel_time_1d(distance: float, closing_speed: float,
                   speed_cap: float, accel_cap: float) -> float:
    """Fixed-LOS travel-time *heuristic*; not a 2-D feasibility certificate."""
    if distance <= 0: return 0.0
    if speed_cap <= 0: return math.inf
    if accel_cap <= 0: raise ValueError('accel_cap must be positive')
    # Input must obey the estimator's speed-cap assumption.
    s = min(float(closing_speed), speed_cap)
    accel_time = (speed_cap - s) / accel_cap
    accel_dist = s * accel_time + 0.5 * accel_cap * accel_time**2
    if distance <= accel_dist:
        return (math.sqrt(s*s + 2 * accel_cap*distance) - s) / accel_cap
    return accel_time + (distance - accel_dist) / speed_cap


@dataclass(frozen=True)
class Config:
    dt: float = 0.1
    vmax: float = 3.0
    umax: float = 1.5
    safe_distance: float = 3.0
    barrier_distance: float = 3.5
    capture_radius: float = 1.0
    release_max_age: float = 4.5
    time_margin: float = 0.3
    hold_horizon: float = 25.0
    deadline: float = 90.0
    velocity_gain: float = 1.4
    kappa1: float = 1.5
    kappa2: float = 2.5
    braking: float = 1.5
    # Set to 1e6 to match paper parameters; scipy fallback is more stable
    # for this demonstration at 1e4. Backend should be reported in logs.
    slack_weight: float = 1e4
    solver: str = 'scipy_slsqp'


@dataclass(frozen=True)
class TargetMessage:
    position: np.ndarray
    velocity: np.ndarray
    timestamp: float


@dataclass
class ControllerState:
    positions: np.ndarray   # N x 2
    velocities: np.ndarray  # N x 2
    phase: str = 'hold'
    terminal_time: float | None = None

    def __post_init__(self):
        self.positions = np.asarray(self.positions, dtype=float).copy()
        self.velocities = np.asarray(self.velocities, dtype=float).copy()
        if self.positions.ndim != 2 or self.positions.shape[1] != 2:
            raise ValueError('positions must have shape (N,2)')
        if self.positions.shape != self.velocities.shape:
            raise ValueError('velocities must match positions')


class AACController:
    def __init__(self, config: Config = Config()):
        self.cfg = config
        if config.solver not in ('scipy_slsqp', 'cvxpy_ecos'):
            raise ValueError('solver must be scipy_slsqp or cvxpy_ecos')

    def estimate_targets(self, now: float, messages: Sequence[TargetMessage]):
        ages = np.array([now - m.timestamp for m in messages], dtype=float)
        if np.any(ages < -1e-8): raise ValueError('target message timestamp is in the future')
        estimates = np.array([m.position + max(0, a)*m.velocity
                              for m, a in zip(messages, ages)])
        velocities = np.array([m.velocity for m in messages], dtype=float)
        return estimates, velocities, ages

    def release_candidate(self, now: float, state: ControllerState,
                          estimates: np.ndarray, target_v: np.ndarray,
                          ages: np.ndarray) -> float | None:
        c=self.cfg
        if np.any(ages > c.release_max_age) or np.any(ages < 0): return None
        earliest=[]; nominal=[]
        for i in range(len(estimates)):
            rho=uncertainty_radius(float(ages[i]))
            los=estimates[i]-state.positions[i]
            dist=float(np.linalg.norm(los))
            n=los/max(dist,1e-8)
            closing=float(n @ (state.velocities[i] - target_v[i]))
            cap=c.vmax-float(n @ target_v[i])
            # one-dimensional LOS braking screen as defined in manuscript
            remaining=max(0., dist-c.capture_radius)
            stop=max(0.,closing)**2/(2*c.braking)
            if remaining < stop: return None
            earliest.append(travel_time_1d(dist+rho,closing,cap,c.umax))
            nominal.append(travel_time_1d(dist,closing,cap,c.umax))
        upper=min(c.deadline-now,c.hold_horizon)
        lower=max(earliest)
        if not math.isfinite(lower) or lower>upper:return None
        # clamp nominal slowest ETA plus timing margin to common interval
        return float(np.clip(max(nominal)+c.time_margin, lower,upper))

    def nominal_control(self, now: float, state: ControllerState,
                        estimates: np.ndarray, target_v: np.ndarray):
        c=self.cfg
        if state.phase=='hold':
            return np.array([-saturate(c.velocity_gain*v,c.umax) for v in state.velocities])
        theta=max(float(state.terminal_time-now),c.dt)
        out=[]
        for p,v,pt,vt in zip(state.positions,state.velocities,estimates,target_v):
            predicted_terminal=pt+theta*vt
            reference_velocity=saturate((predicted_terminal-p)/theta,c.vmax)
            out.append(saturate(c.velocity_gain*(reference_velocity-v),c.umax))
        return np.stack(out)

    def filter_control(self, state: ControllerState, nominal: np.ndarray):
        """Solve softened pairwise high-order CBF constraints; diagnostics returned.

        Positive slack, sampled updates and projected velocity mean that even
        solver success DOES NOT certify continuous-time collision avoidance.
        """
        c=self.cfg
        n=state.positions.shape[0]
        pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
        if not pairs:return nominal.copy(),dict(success=True,max_slack=0.,active=False,
                                                 solver='none',status='no_pairs')
        # Pairwise HOCBF: A_i u_i + A_j u_j + eta >= rhs
        A=np.zeros((len(pairs),2*n))
        rhs=np.zeros(len(pairs))
        for row,(i,j) in enumerate(pairs):
            dp=state.positions[i]-state.positions[j]
            dv=state.velocities[i]-state.velocities[j]
            h=float(dp@dp-c.barrier_distance**2)
            dh=float(2*dp@dv)
            rhs[row]=-2*float(dv@dv) -(c.kappa1+c.kappa2)*dh -c.kappa1*c.kappa2*h
            A[row,2*i:2*i+2]=2*dp
            A[row,2*j:2*j+2]=-2*dp
        if c.solver=='cvxpy_ecos':
            try:
                import cvxpy as cp
            except ImportError as exc:
                raise RuntimeError('Optional CVXPY/ECOS not installed') from exc
            u=cp.Variable((n,2))
            slack=cp.Variable(len(pairs),nonneg=True)
            constraints=[cp.norm(u[i],2)<=c.umax for i in range(n)]
            constraints += [A@cp.reshape(u,(2*n,),order='C')+slack >=rhs]
            objective=.5*cp.sum_squares(u-nominal)+.5*c.slack_weight*cp.sum_squares(slack)
            problem=cp.Problem(cp.Minimize(objective),constraints)
            try:
                problem.solve(solver='ECOS', abstol=1e-8, reltol=1e-8, max_iters=200)
                if problem.status not in ('optimal','optimal_inaccurate') or u.value is None:
                    raise RuntimeError(f'ECOS status: {problem.status}')
                solution=np.array(u.value)
                slack_vals=np.maximum(0,np.array(slack.value))
                status=str(problem.status);ok=True
            except Exception as exc:
                solution=nominal.copy();slack_vals=np.full(len(pairs),math.nan)
                status=f'failed:{str(exc)[:120]}';ok=False
        else:
            # scipy SLSQP *illustrative alternative solver*, NOT manuscript ECOS
            x0=np.concatenate([nominal.ravel(),np.maximum(0,rhs-A@nominal.ravel())])
            def objective(x):
                v=x[:2*n]-nominal.ravel()
                return .5*(v@v +c.slack_weight*(x[2*n:]@x[2*n:]))
            def gradient(x):
                return np.concatenate([x[:2*n]-nominal.ravel(),c.slack_weight*x[2*n:]])
            constraints=[{'type':'ineq','fun':lambda x,A=A,rhs=rhs:A@x[:2*n]+x[2*n:]-rhs,
                          'jac':lambda x,A=A:np.hstack([A,np.eye(len(pairs))])}]
            for i in range(n):
                constraints.append({'type':'ineq',
                  'fun':lambda x,i=i:c.umax**2-x[2*i:2*i+2]@x[2*i:2*i+2],
                  'jac':lambda x,i=i:np.r_[np.zeros(2*i),-2*x[2*i:2*i+2],np.zeros(len(x)-2*i-2)]})
            res=minimize(objective,x0,method='SLSQP',jac=gradient,
                         bounds=[(-c.umax,c.umax)]*(2*n)+[(0,None)]*len(pairs),
                         constraints=constraints,
                         options={'ftol':1e-7,'maxiter':200,'disp':False})
            solution=res.x[:2*n].reshape((n,2)) if res.success else nominal.copy()
            slack_vals=np.maximum(res.x[2*n:],0) if res.success else np.full(len(pairs),math.nan)
            ok=bool(res.success)
            status=str(res.message)
        return solution,dict(success=ok,max_slack=float(np.nanmax(slack_vals)) if ok else None,
                             active=bool(np.max(np.linalg.norm(solution-nominal,axis=1))>1e-5),
                             solver=c.solver,status=status)

    def step(self, now: float, state: ControllerState,
             messages: Sequence[TargetMessage]):
        c=self.cfg
        if len(messages)!=len(state.positions):raise ValueError('one target message per UAV required')
        estimates,vt,ages=self.estimate_targets(now,messages)
        released=False
        if state.phase=='hold':
            candidate=self.release_candidate(now,state,estimates,vt,ages)
            if candidate is not None:
                state.phase='terminal';state.terminal_time=now+candidate;released=True
        nominal=self.nominal_control(now,state,estimates,vt)
        safe,diagnostics=self.filter_control(state,nominal)
        # Explicit-Euler position and bounded projected velocity, as in paper
        p_next=state.positions+c.dt*state.velocities
        v_next=np.stack([saturate(v+c.dt*u,c.vmax) for v,u in zip(state.velocities,safe)])
        next_state=ControllerState(p_next,v_next,state.phase,state.terminal_time)
        diagnostics.update(time=float(now),released=released,age_max=float(max(ages)),
                           nominal_u_norm_max=float(np.max(np.linalg.norm(nominal,axis=1))))
        return next_state,diagnostics
