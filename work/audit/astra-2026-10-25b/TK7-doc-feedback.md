# TK7 — changes that would save the next reviewer time

DOCUMENTED against18b6cef on2026-10-25:

1. REVIEW.md:3 still says round6/24-Oct; AUDIT.md:3 says currentround6. TASKS.md correctly says round7/25-Oct. Put the same round and exact design baseline in all three headers. The docs checker passes because it checks IDs/counts/paths,not this semantic agreement.
2. REVIEW.md setup ends with plain `checks/run_all.py`,which writes designer STATE.md/last_run/checks-out. TASKS.md correctly says `--report`. Show reviewer mode in setup itself. TK5-isolation.json verifies its protected outputs. It also regenerates deterministic rotation tables and module candidates; it does not promise zero filesystem writes everywhere.
3. TASKS.md TK4 and AUDIT.md round6 response include LM2904 in the+5V sink discussion. Actual U6.8 is VOP12. Name the direct branches (TJA1051,REF3030,module) and distinguish A8 module-branch versus aggregate regulator-output measurements. See R7-S2.
4. Add exact manufacturer datasheet URLs/revisions to the inventory. C844867 has a thermal footnote; multiple unrelated makers sell BZT52C18 with different ratings. Correct sources/limits are in TK3-surge-review.md. A supplier500mW label or generic TVS name does not establish the actual400ms envelope.
5. `ordering.md:74` permits a plain same-value/package resistor swap to skip an audit,while step3 protects R9's HP rating. Require equivalent **power/pulse/thermal limits**,not merely1206/1k. A250mW substitution would again face0.480/0.250=192% in the illustrative envelope. Step3 already warns against it; this is a consistency NOTE,not evidence a bad substitution happened.

What worked: ordered tasks,per-stage commits,raw prior reproductions,cached EasyEDA transforms,report-only checks,and local licensed model availability. Prior findings remained separate artifacts rather than being treated as facts.

No designer documentation or circuit source edits made. These are proposed corrections.
