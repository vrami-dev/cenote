# Benchmarks

One machine, all runs 2026-10-09 to 2026-10-18:
- RTX 3090 24 GB (PCIe 4.0 x16), Ryzen 7 5800X (8 cores / 16 threads), 128 GB DDR4-3200 (4 x 32 GB, dual channel)
- Samsung 990 EVO Plus NVMe, Windows 11 Pro, NVIDIA driver 616.92

These are speed and function results on one rig. They are not quality benchmarks; the quality numbers quoted in this
repo are from the quants' own cards or from other people's evaluations, and say so where they appear.

## DeepSeek-V4.1-Flash-1017 (Xolotl): routing modes

Model: lxe's dsx 2-bit build (148.1 GB) with IndrasMirror's 1017 DSpark draft, `deepseek/strata-ds41-1017dsx-win.json`.

**Method** ([bench/abba_smart.py](../bench/abba_smart.py)): one fresh server; every mode switched per request through
`strata_tune`, so anything else loading the PC slows all modes alike. Three prompts (a 350-word insurance explainer, an
LRU cache class with asserts, 12 rows of CRM JSON). Per prompt: one warm-up, then the five modes in a rotation and its
reverse. Greedy, thinking off, 400 tokens. Medians of 6 requests per mode.

| Mode | Prose | Code | Agent | Avg tok/s | Picks swapped vs exact | Router weight kept | Expert lookups from VRAM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| exact (no nudge) | 9.0 | 10.6 | 9.6 | 9.7 | 0% | 100% | 58.9% |
| fast (0.5 / 0.3) | 18.0 | 25.0 | 22.0 | 21.7 | 37.1% | 72.2% | 88.4% |
| **light (0.25 / 0.15), the default** | 15.9 | 22.4 | 19.1 | **19.1** | 26.1% | 81.3% | 81.0% |
| smart (protect 2, pool 12, 1.0 / 0.6) | 15.6 | 19.4 | 17.4 | 17.5 | 18.6% | 87.0% | 71.7% |
| smart-half (protect 2, pool 12, 0.5 / 0.3) | 14.9 | 18.0 | 16.0 | 16.3 | 16.1% | 89.2% | 68.9% |

Raw: [bench/results/2026-10-18-routing-modes.json](../bench/results/2026-10-18-routing-modes.json). The answer texts are left out (the agent prompt asks for realistic fake contact data); `text_chars` keeps their length.

- **Why light is the default:** 12% slower than fast for 11 points fewer swapped picks, and it is the only setting with a
  real quality score: Xolotl's author measured the same strength at 85.2% API top-1 against 86.2% for exact routing (RTX
  4090, September build). The route meter is a proxy, not a score.
- **Smart routing** keeps more of the router's weight but serves fewer lookups from VRAM, so it costs speed. It looks like
  another point on the same speed/fidelity curve.
- **Earlier two-mode runs** with the same method (prompts alternated by a trailing space): fast 22.8 vs exact 10.4 tok/s,
  fast 22.9 vs light 17.8 tok/s ([fast-vs-exact](../bench/results/2026-10-18-fast-vs-exact.json),
  [fast-vs-light](../bench/results/2026-10-18-fast-vs-light.json); their expert counts came back empty from a log-offset
  bug in that harness version, the speeds are unaffected).
- **The 1017 draft vs the September draft:** same acceptance on these prompts (tokens per pass: code 3.67 vs 3.70, agent
  2.96 vs 2.78, prose 1.67 vs 1.71).

## DeepSeek-V4.1-Flash, September build (Xolotl): config tuning

Model: IndrasMirror's September GSQ build (163 GB). Method: a fresh server per variant, one warm-up, the same three
prompts, 3 runs each, greedy, thinking off, 400 tokens, median.

| Variant | Prose | Code | Agent | Average |
| --- | ---: | ---: | ---: | ---: |
| 64 GiB arena (Xolotl's served config) | 13.0 | 17.4 | 15.7 | 15.4 |
| 72 GiB arena | 14.3 | 20.7 | 18.4 | 17.8 |
| 80 GiB arena | 14.4 | 20.2 | 17.7 | 17.4 |
| 72 GiB, DSpark off | 16.5 | 19.1 | 18.0 | 17.9 |
| 72 GiB + `STRATA_TIER_BATCH_PCIE=0.75` (repeat run) | 14.7 | 22.1 | 18.8 | **18.5** |

Raw: [round2](../bench/results/2026-10-18-september-round2.jsonl), [round3](../bench/results/2026-10-18-september-round3.jsonl).
+19% from two settings. A fresh 13,294-token prompt read in 63.45 s (209.5 tok/s).

## GLM-5.3-Flash (Project Maya 1.1.15, Maya-S24)

Maya's own 16-test function suite run against the server: decode 17.6 / 16.9 / 17.8 tok/s on three stories; 30K prompt
at 1,182 tok/s; 115K prompt in 99.3 s; cached follow-up 2.2 s; back to a parked 115K conversation 3.7 s; 15 of 16 passed.

## Swift 1.5 (Strata 0.1.45, elastic VRAM)

Two runs: story 94.8 / 94.2 tok/s, code 102.2 / 101.7, document summary 95.1 / 92.6, fresh 16K prompt 2,256 / 2,249
tok/s. 116,201-token prompt in 47.3 s. Strata's 17-test suite 17/17, vision 4/4. Against Strata 0.1.41 interleaved on
the same rig: story +15%, code +33%.

## Three models, one suite (2026-10-09)

The same 16 tasks (coding tasks unit-tested), one model at a time:

| | Qwen3.8-Flash-Next IQ3_S | Swift 1.5 IQ3_S | GLM-5.3-Flash Maya-M |
| --- | --- | --- | --- |
| Total | 15/16 | 15/16 | **16/16** |
| Decode, three stories (tok/s) | 78.8 / 96.0 / 90.3 | 59.4 / 71.5 / 78.4 | 12.3 / 12.9 / 12.9 |
| ~115K prompt | 44 s | 45 s | 101 s |
| Hardest coding task | ran out at 16,000 thinking tokens | ran out at 15,474 | passed, 1,256 tokens |

Engine versions then: Strata 0.1.41 and Maya 1.0.27. Swift's decode was slower than Qwen's on that day (its expert
profile ranked base Qwen's routing); its 0.1.45 numbers are above.
