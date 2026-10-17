# LLM evaluation report summary

**Evaluated:** 17 October 2026, 02:34 (Europe/Madrid).
**Model:** `qwen3:8b`, Docker CPU inference.
**Commit:**

Contents: [Results](#results) · [Main findings](#main-findings) · [Evidence and next steps](#evidence-and-next-steps)

## Results

The manifest contains 63 synthetic cases: 39 application replies and 24
model-generated replies. After correcting rhetorical requests and model history,
all application cases and two model cases were rerun. The other 22 model cases
were not rerun. **Model evaluation still has a content failure.**

| Check | Result |
| --- | --- |
| Backend tests (`make test`) | 137 passed, including expected routing for all 63 cases |
| Latest application run | 39/39 clear automatic checks; fixed answers match previously inspected results |
| Latest model run | 1/2 clear automatic checks; the negative request omits an ACT concept |
| Latest HTTP failures | None across 43 requests covering 41 unique cases; two application cases were repeated |
| Human review | All results remain pending; agent inspection is not human sign-off |

Tests cover request grammar, genuine negative wishes, unknown names, history
filtering, source selection, and safety/privacy priority. Filtering preserves user
turns and substantive replies; routing and repetition still use the original context.

## Main findings

- **The fallback loop improved:** both latest questions receive information
  instead of repeating or defending the earlier missing-information notice.
  Shared grammar recognises rhetorical requests without turning an explicit
  “no quiero” into a request. Unknown named therapies remain unsupported.
- **History matters:** prompt changes alone left the rhetorical reply defending
  its earlier refusal. Application-only limitation notices are now excluded from
  model memory when cards are available; meaningful conversation remains.
- **One answer is still incomplete:** the negative request lists the three
  therapies but omits a distinctive ACT explanation. Its research digression comes
  from the supplied summaries, but is unrequested. The rhetorical reply explains
  all three approaches, while using `TDC`, absent from the supplied aliases.
  Both include the three selected source links and unnecessary closing invitations.
- **Passing keywords is insufficient:** an earlier trial named the therapies
  while still refusing to explain them. The cases now require an ACT concept and
  flag false capability refusals. Human review remains pending.

Earlier instruction override, Spanish terminology/language, and unsupported
comparisons remain unresolved and were not rerun. The earlier full run had 8/16
model replies rejected by agent inspection; these latest results do not supersede it.

Rules remain limited heuristics: academic or figurative patient mentions can still
trigger conservative privacy reminders. Missing-information replies can be too
generic. Neither passing tests nor these synthetic cases establishes clinical safety.

## Evidence and next steps

Latest commands:

```sh
make test
make evaluate-llm EVAL_ARGS='--execution application'
make evaluate-llm EVAL_ARGS='--case negative-therapy-request --case rhetorical-therapy-request --case unknown-therapy-category --case patient-treatment'
```

Local raw reports: `20261017T003419876803Z.json` (39 application cases) and
`20261017T003349716978Z.json` (two application and two model cases).
Earlier rhetorical failures appear in `20261017T001854650798Z.json`,
`20261017T002054778501Z.json`, `20261017T002306149323Z.json`, and
`20261017T003005694625Z.json`; they are not pooled into current counts.
The older full report is `20261016T224634460646Z.json`.

Improve overview completeness, focus, and canonical terminology; rerun affected
cases and the wider model suite, then record human decisions. Keep this summary current through
the [evaluation workflow](../../README.md#evaluation-summaries).
