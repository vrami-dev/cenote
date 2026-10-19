# Qwen3.8-Flash-Next (Swift 1.5) on Strata 0.1.45

The daily driver on the test rig: fast, 262K context, vision. It runs Qwen3.8-Flash-Next as Swift 1.5, UkisAI's
fine-tune that cuts the base model's overthinking (63.4% fewer thinking tokens on GPQA-Diamond per its card, at about
the same score).

| | |
| --- | --- |
| Model | Swift 1.5, UkisAI's fine-tune of Qwen3.8-Flash-Next (Swift Open License 1.0) |
| Quant | IQ3_S GSQ-RCO by ukisai, 83.7 GB ([huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO-GGUF)) |
| Engine | [Strata](https://github.com/Niko1221/Strata) 0.1.45 by Niko1221 |
| Config | [strata-swift-iq3_s.json](strata-swift-iq3_s.json): port 8080, 262,144 context, INT8 KV with KV streaming (32,768 resident), MTP drafts (`--spec 4`), GPU vision, elastic VRAM |
| Start | `scripts\start-swift.cmd` (or `scripts\start-swift.cmd uncensored` for SC117's abliterated Swift, [config](strata-swift-uncensored-iq3_s.json)) |

## Numbers (test rig, Strata 0.1.45 with elastic VRAM, two runs)

| Test | Run 1 | Run 2 |
| --- | ---: | ---: |
| Story, greedy | 94.8 tok/s | 94.2 tok/s |
| Code, greedy | 102.2 tok/s | 101.7 tok/s |
| Document summary (6.8K prompt) | 95.1 tok/s | 92.6 tok/s |
| Fresh 16K prompt | 2,256 tok/s | 2,249 tok/s |

- A 116,201-token prompt read in 47.3 s (2,482 tok/s); cached follow-ups answer in under half a second.
- Strata's 17-test function suite: 17 of 17. Vision (shapes and exact text): 4 of 4.
- Against Strata 0.1.41 on the same rig: story +15%, code +33%, prompts +5%. The gain holds at equal cache size, so it is
  the engine, not only the bigger expert cache.

## Setup

1. Unpack Strata 0.1.45 to `D:\strata-0.1.45` and set up its Python environment as its README describes. On the test
   rig the model files were placed by hand rather than by Strata's setup scripts.
2. Download the IQ3_S GGUF (2 shards) and Swift's mmproj to `D:\strata-models\swift-1.5`.
3. Build the expert pack with Strata's `tools/iq_pack.py`. Strata's setup lists Swift IQ3_S as unsupported
   ([#1651](https://github.com/Niko1221/Strata/issues/1651)); it loads and runs anyway.
4. Edit the paths in the config. The MTP draft (`--mtp`) is base Qwen3.8-Flash-Next's draft layer from Strata's own
   Qwen setup. Swift accepts it as well as base Qwen does (65.0% vs 63.7% acceptance).
5. `scripts\start-swift.cmd`, then http://127.0.0.1:8080/v1.

## Notes from the rig

- **Keep one batch slot.** Strata's `"parallel": N` slots were 12-25% slower for three agents at once on this CPU
  (Ryzen 7 5800X): slots switch off the route tail skip, take expert-cache room, and each batch window waits on the
  CPU. Pi Desktop sending three agents to one slot was the fastest mode.
- **Elastic VRAM** starts the image encoder with the first picture and grows the expert cache (about 7,750 slots
  instead of 5,500-7,100), which also removed a start-up race on Windows.
- **xhigh is the top thinking level** for the Qwen family (low / medium / xhigh). Hard coding tasks at xhigh can need
  more than 8,192 output tokens; the config allows 32,768.
- Swift used 44% fewer thinking tokens than base Qwen on one of our coding tasks; on the 16-task suite both scored
  15/16. An independent pre-registered test found Swift answers more trick questions it should refuse (refusal
  0.65 vs 0.74), so don't use it as a source of facts without a check.
