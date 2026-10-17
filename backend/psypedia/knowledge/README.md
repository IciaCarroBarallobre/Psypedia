# Demo knowledge base

`topics.json` contains author-written summaries of public pages, not clinical
manual excerpts. The cards have not undergone clinical expert review.

## Table of Contents

- [Sources and scope](#sources-and-scope)
- [Integration](#integration)
- [Extending the cards](#extending-the-cards)

## Sources and scope

| Card | Public source |
| --- | --- |
| CBT / TCC | [NHS: Cognitive behavioural therapy](https://www.nhs.uk/tests-and-treatments/cognitive-behavioural-therapy-cbt/) |
| ACT | [ACBS: About ACT](https://contextualscience.org/about_act) |
| DBT | [Behavioral Tech Institute: What is DBT?](https://behavioraltech.org/dialectical-behavior-therapy-dbt/) |
| Precision Psychology | [Purgato et al.: precision psychology paradigm](https://doi.org/10.1017/S2045796021000500) |

The local wiki names CBT/TCC, ACT, and DBT, and mentions Precision Therapy without
a selected source or definition. The Precision Psychology research card is an
additional demo topic, **not a synonym for Precision Therapy**.

Each card records its ID, category, canonical name, aliases, summary, source title/URL, and
check date. A check date records a source review, not a guarantee of current or
clinically complete information.

## Integration

See [knowledge and prompting responsibilities](../../LLM_AND_PROMPTING.md#knowledge-and-prompting-folders)
for how retrieval, context formatting, and model instructions fit together.

Specific names take priority. Broad requests such as “terapias” select the
`psychotherapy` category (CBT, ACT, DBT); Precision Psychology is `research`.
Shared noun/adjective patterns also recognise psychological or psychotherapeutic
approaches, coordinated descriptions, and rhetorical requests without listing
each question. The request prefix is separated from the topic; a negative
auxiliary can ask for an explanation, while an explicit refusal is not an overview request.
Unknown named qualifiers do not trigger a category overview. In mixed questions,
known cards are retained: the service adds a limitation notice and requests an
explanation of the documented part only. Unknown or pending topics alone receive
a fixed limitation. Selection and named-gap detection both belong to `retrieval.py`.

This is lexical demo retrieval, not semantic RAG. A matching alias or category does not imply
that the card answers every subquestion; source links identify input cards rather
than verified support for every generated claim.

## Extending the cards

Add precise aliases, a unique ID, a category, a short paraphrased summary, and source metadata.
`covered_topics` explicitly declares sensitive educational coverage (`suicide`,
`self_harm`, `injury`); current cards have empty lists. Add a value only after reviewing
content and sources for that scope. The flag controls routing, not clinical validation.
Verify that the source supports each fact; do not fill gaps with invented content.
After card or retrieval changes, update tests, rerun relevant synthetic cases, review
the answers, and update the same [results summary](../../evaluation/reports/summary.md).
Commit that update following the [summary workflow](../../README.md#evaluation-summaries),
including findings and pending review.
Manual ingestion and passage-level retrieval remain future work.
