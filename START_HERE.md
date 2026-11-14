# START HERE

**This is the complete prepared package you can publish as a transparent archive + new reference code.** The original experiment-generating code is still missing, and the package cannot fully reproduce the manuscript's original tables.

1. Read `README.md` and `docs/AUDIT_FINDINGS.md`.
2. Run `python3 analysis/verify_checksums.py`.
3. Install new-code dependencies with `python3 -m pip install -r requirements-reference.txt`.
4. Test reference code: `python3 -m unittest discover -s tests -v`.
5. Run demo: `python3 -m reference_controller.demo --output reference_runs`.
6. Follow `overleaf/OVERLEAF_INSTRUCTIONS.md` to publish this **directory's contents** on GitHub.
7. After publication, replace the `\dataavailability{}` command in Overleaf with `overleaf/OVERLEAF_DATA_AVAILABILITY_AFTER_PUBLICATION.tex` (edit GitHub username first).
8. Do not tell the editor the original experiment code has been recovered; do not claim that sync-flag anomalies are solved.
