# Diagnosis scratchpad

| symptom (from telemetry) | which requests | suspected cause | config fix? | wrapper fix? |
|---|---|---|---|---|
| High tokens / cost | all | verbose_system + temp 1.6 + premium tier | yes | cache |
| Wrong totals | coupon+shipping orders | temperature 1.6 | yes | — |
| Tool errors on Hà Nội | pub-11 | normalize_unicode off | yes | NFC sanitize |
| MacBook always OOS | pub-02, pub-10 | catalog_override | yes | — |
| Answers degrade turn 6+ | long sessions | session_drift_rate | yes | session reset |
| Repeated check_stock | some | loop_guard off | yes | log repeated_tools |
| Email echoed in answer | pub-13 | redact_pii off + bad prompt | yes | output redact |
| Tool call failures | intermittent | tool_error_rate 18%, no retry | yes | retry + cache |
| Extra tool calls | many | tool_budget=0 | yes | — |
| Fake total OOS items | pub-05, pub-07 | bad prompt | prompt | — |
| Obey GHI CHU price | private phase | injection in notes | prompt | sanitize input |
