# Phase 3 Deliverables Checklist

Use this checklist before final thesis submission or supervisor demonstration.

## Prototype

- [ ] Flask app starts with `python app.py`.
- [ ] Webcam mode works with `USE_WEBCAM=true`.
- [ ] Dashboard login works when `DASHBOARD_AUTH_ENABLED=true`.
- [ ] Arm/disarm buttons work.
- [ ] Manual snapshot works.
- [ ] Person detection creates event snapshots while armed.
- [ ] Telegram alert delivery works.
- [ ] Cooldown prevents repeated alerts.
- [ ] `.env` is not committed.
- [ ] Runtime folders `events/` and `logs/` are not committed.

## Source Code

- [ ] `README.md` explains setup, configuration, camera mode, Telegram, voice webhook, and evaluation commands.
- [ ] `.gitignore` excludes secrets and runtime evidence.
- [ ] `requirements.txt` is up to date.
- [ ] Model files are present in `models/`.
- [ ] Scripts are present for evaluation and monitoring.
- [ ] Internal demo-only documents are not part of the final GitHub deliverable.

## Testing Evidence

- [ ] `data/phase3_trials_template.csv` is filled with official Phase 3 trial results.
- [ ] `logs/phase3_trials_summary.json` is generated from `evaluate_trials.py`.
- [ ] `docs/phase3_results_report.md` is generated from `generate_phase3_report.py`.
- [ ] `logs/status_monitor.csv` is collected for stability evidence.
- [ ] Usability observations are recorded in `data/phase3_usability_checklist.csv`.
- [ ] Any included screenshots do not expose tokens, chat IDs, private faces, or private room details.

## Thesis Documentation

- [ ] Test environment is described.
- [ ] Accuracy metrics are reported with TP, FP, FN, TN, precision, recall, F1, accuracy, and specificity.
- [ ] Latency results are reported.
- [ ] Stability results are reported.
- [ ] Usability results are summarized.
- [ ] Limitations are discussed honestly.
- [ ] Security and privacy considerations are discussed.
- [ ] Future work recommendations are included.

## Final Safety Check

- [ ] Rotate the Telegram bot token if it appeared in any screenshots, browser history, chat logs, or recordings.
- [ ] Confirm `.env` is still ignored by Git.
- [ ] Confirm no event images with private content are committed.
- [ ] Run `git status` and review every changed file before pushing.
