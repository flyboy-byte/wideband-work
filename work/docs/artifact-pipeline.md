# Artifacts in the autonomous loop: what worked, what didn't (2026-10-23)

Question from the owner: would putting artifacts (published pages) into the autonomous workflow help? Short answer: yes for
one job, review from a phone; no as a replacement for the files that carry state.

## What was built
`checks/report.py` reads `checks/last_run.json`, `report/tests.json` and `renders/<REV>/*.png` and writes one self-contained
`report/index.html` (images downscaled to JPEG and embedded, 491 KB). The session publishes that file with the Artifact tool;
publishing the same path again keeps the URL. Template: `checks/report_template.html`. Page: see STATE.md "Review pages".

## Why it helps
- The owner reviews from his phone. Before this, the only view of the board was a PNG in the transcript or a file on disk.
- The page is made from the same data the gates use (`last_run.json`), so it can't claim a pass that `run_all.py` didn't record.
- The what-if tests (`checks/whatif_route.py`) give the page something to show besides a count: the before / after crops of the
  one open connection.

## Where it does not help
- It is a view, not a source of truth. `STATE.md`, `HANDOFF.md` and the check table stay the state; the page is rebuilt from them.
- Publishing is an agent step (a tool call), not something a Python script or a hook can do. So the loop has to say when:
  after `run_all.py` at a pause point, and when the owner asks. A stale page is the failure mode: its subtitle carries the date
  and commit, and `report.py` takes both from `last_run.json`.
- The page is private (owner's account). Sharing, or putting it in front of Codex, is the owner's decision. Codex gets the audit
  pack folder (`work/audit/`) instead, which is plain files.
- No database or capabilities used: the open questions are not collected on the page yet. The skill's `review.html` template (with
  the `db` capability) does that; adopt it when there are enough owner questions to batch.

## Suggested rule for the loop
At each pause point: `run_all.py` → `report.py` → republish the same file path → put the URL in `STATE.md`. Don't publish on every
run. Rebuild the page only from a state that has passed through the checks.
