# GLM-5.3-Flash on Project Maya 1.1.15

The careful one: slower than Swift, and the best scorer on the test rig's coding suite.

| | |
| --- | --- |
| Model | GLM-5.3-Flash by Zhipu AI ([zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash), MIT), a 320B MoE |
| Quant | Maya-S24 by peasantsmith, 94.7 GB ([huggingface.co/peasantsmith/GLM-5.3-Flash-Maya-GGUF](https://huggingface.co/peasantsmith/GLM-5.3-Flash-Maya-GGUF)). Its card: 97.7% of FP8 zero-shot accuracy, KL 0.444 vs FP8, built for 24 GB cards |
| Engine | [Project Maya](https://github.com/mw00/project-maya) 1.1.15 by mw00 (Strata-derived, GLM-specific) |
| Config | [maya-maya-s24.json](maya-maya-s24.json): port 8090, 131,072 context, vision, MTP drafts |
| Start | `scripts\start-glm.cmd` |

## Numbers (test rig, Maya 1.1.15 + Maya-S24, 16-test suite)

| Test | Result |
| --- | ---: |
| Decode, three stories | 17.6 / 16.9 / 17.8 tok/s |
| 30K-token prompt | 1,182 tok/s |
| 115K-token prompt | 99.3 s (1,121 tok/s) |
| Follow-up on the cached 115K conversation | 2.2 s |
| Back to a parked 115K conversation | 3.7 s |
| Suite | 15 / 16 (one coding task failed on `'1h30m'` parsing) |

- On Maya 1.0.27 with the larger Maya-M quant the same suite scored 16/16 at 12.3-12.9 tok/s. 1.1.15 + S24 is about 40%
  faster.
- GLM solved the unit-tested coding tasks with about 8x fewer thinking tokens than the Qwen-family models.

## Setup

1. Install Project Maya 1.1.15 to `D:\project-maya-1.1.15` per its README (Visual Studio 2022 Build Tools and CUDA
   12.8 to build). Its installer can fetch the quant (`Maya-S24`).
2. Copy [maya-maya-s24.json](maya-maya-s24.json) and edit the paths.
3. `scripts\start-glm.cmd`, then http://127.0.0.1:8090/v1.

## Notes from the rig

- **RAM:** Maya keeps most of the model in pinned RAM. With 128 GB, about 4-15 GB stays free while it runs. Close heavy
  apps; a big agent run once pushed free RAM to 1.7 GB and Windows into the page file.
- **Calibration:** Maya's pre-check refuses when the GPU has more than 1 GiB in use, and a Windows desktop on the same
  card uses about 1.07 GB. The engine defaults were already the fastest setting on this rig.
- **Single-3090 reports of ~26 tok/s** come from quad- or eight-channel RAM machines. This rig is dual-channel DDR4.
- **Uncensored:** peasantsmith's Maya-M-Derisked (116 GB) runs on the same engine. It is downloaded on the test rig and
  not measured yet; its own card says its drift evaluation is not done.
