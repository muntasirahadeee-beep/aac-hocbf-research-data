# Connecting a verified public GitHub repository to Overleaf

## 1. Publish the directory contents, not the compressed ZIP

1. Extract `AAC_HOCBF_Research_Data_Reference_Code_v1.0.zip`.
2. Open the extracted folder in VS Code. From `Terminal > New Terminal`, run:
   ```bash
   python3 analysis/verify_checksums.py
   python3 analysis/audit_all_seed_metrics.py
   python3 -m pip install -r requirements-reference.txt
   python3 -m unittest discover -s tests -v
   python3 -m reference_controller.demo --output reference_runs
   ```
3. Inspect `docs/AUDIT_FINDINGS.md` and `docs/REPRODUCIBILITY_GAPS.md`; do not claim full reproduction is achieved.
4. Create a new *public empty* GitHub repository named `aac-hocbf-research-data-reference-code`. Do not enable auto-generated README or license.
5. Run from the unzipped folder:
   ```bash
   git init
   git add .
   git commit -m "Release archived AAC-HOCBF results and independent reference implementation"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/aac-hocbf-research-data-reference-code.git
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` with your own account. If Git asks for a username/email set `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`. Sign in through VS Code or GitHub CLI; never put an access token in the repository.
6. Open the GitHub URL in a private/incognito window and verify `README.md`, `data/`, `analysis/`, `reference_controller/`, `tests/`, and `docs/` are visible.
7. If you recover actual experiment-generating code, publish it in a **separate `original_experiment_code/` folder** with dependencies, exact run commands and logs, only after confirming provenance.

## 2. Use a short, accurate statement in Overleaf

Open the main `.tex` document in Overleaf, find `\dataavailability{...}`, and replace that entire command with the code in `overleaf/OVERLEAF_DATA_AVAILABILITY_AFTER_PUBLICATION.tex`, replacing `YOUR_USERNAME` with your real username and checking the link. Do not insert that code until the repository is actually public. Avoid publishing the repository ZIP as a figure or a separate Overleaf image.

This **honest** statement explicitly distinguishes archived experimental outputs from the *independently created* reference implementation; it cannot truthfully claim full historical reproducibility.

## 3. Respond to the Academic Editor

Use `docs/EDITOR_RESPONSE_DRAFT.md` as a *draft*. Edit Comment 6 to provide the public URL and explain that the original historical controller remains unavailable. A data archive plus a new reference implementation may not fully satisfy the editor's explicit request; be prepared to supply the original code if requested.

## 4. When an article is accepted

Consider an archived GitHub release or a Zenodo DOI for a version-specific citation; verify journal guidance and institutional permissions before using those services. This does not replace the need for genuine source provenance.
