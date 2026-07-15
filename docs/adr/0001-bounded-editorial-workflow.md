# ADR 0001: Use a bounded, source-tracked editorial workflow

## Status

Accepted for the initial implementation.

## Context

The system must create regional short-form editorial drafts without requiring users to provide
video. It will eventually research a topic, generate original narration, find short relevant
excerpts, render the video, and request approval.

A single unconstrained model call cannot safely own trend discovery, factual research, source
selection, media acquisition, and publication. It would also make failures difficult to resume
or audit.

## Decision

Use one orchestrator with sequential, bounded stages. Each stage receives a typed artifact and
returns a typed artifact or an explicit failure state.

- Models own semantic decisions such as clustering, editorial angle, script, and visual match.
- Tools own API access, media inspection, cutting, rendering, storage, and upload.
- Validators own schemas, provenance completeness, timing, render integrity, and source-policy
  gates.
- Humans approve the final editorial draft before publication.

India and the United States are independent discovery regions. India defaults to Hinglish and
the United States defaults to English.

Every editorial excerpt must retain source URL, creator, timestamp, used duration, narration
beat, purpose, risk classification, and replacement candidates. Duration limits are workflow
settings, not claims of copyright clearance.

## Consequences

- Jobs can resume from durable checkpoints.
- Model providers and media providers remain replaceable.
- A failed source can be replaced without rewriting the script or rerunning unrelated stages.
- The system can explain why a topic or clip was selected.
- More infrastructure is required than a one-prompt video generator, but the result is testable
  and commercially defensible.
