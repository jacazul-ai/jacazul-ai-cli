---
type: llm
---

- The comparison command runs the benchmark more than once per side, for
  example with `-count 10` or a similar repetition count.
- The answer compares the two runs with `benchstat`, not by reading the
  raw numbers.
- The setup call to `makePayload()` is outside the measured loop.
