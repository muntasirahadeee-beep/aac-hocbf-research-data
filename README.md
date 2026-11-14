# Independently written numerical reference controller

This is a clean-room, independently written mathematical implementation of a small subset of the paper's procedure, created **after** the experiments. It is **NOT the original source** and cannot regenerate manuscript Tables 6–11. Those require the historical simulator, target/scenario generators, network fault processes, seed construction, Gazebo models, and experimental protocol. Source code is published here for explanation, transparency, and future independent testing.

Features implemented: bounded 2-D sampled motion; message timestamps and AoI; manuscript age/radius lookup (not retrained); fixed-LOS travel-time heuristic; common release condition; shared terminal time; nominal terminal guidance; centralized softened pairwise HOCBF filter (SLSQP demonstration or optional CVXPY/ECOS); solver diagnostics and bounded fallback; a two-UAV toy example. The code does not implement the full experimental suite, maneuvering-target validation, 6-DOF flight, delayed inter-UAV state, or proven continuous-time collision avoidance.

The original manuscript used **CVXPY 1.4.2 / ECOS 2.0.12**. The package default is **SciPy SLSQP**, because this demonstration has a lightweight default dependency; different optimization backends may yield different numerical behavior. Optional CVXPY can be installed and selected with `--backend cvxpy_ecos` (versions and dependencies are not guaranteed in arbitrary environments).

Run from repo root:
```bash
python3 -m pip install -r requirements-reference.txt
python3 -m unittest discover -s tests -v
python3 -m reference_controller.demo --output reference_runs --duration 12
```
