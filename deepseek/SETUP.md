# DeepSeek-V4.1-Flash-1017 on Windows

This is the exact path that runs on the test rig. The engine build and the general Windows notes live upstream in
[xolotl/docs/WINDOWS.md](https://github.com/Indras-Mirror/Xolotl/blob/main/docs/WINDOWS.md); this page adds the 1017
model files, the tuned config and the launch scripts.

Test rig: RTX 3090 24 GB, Ryzen 7 5800X, 128 GB DDR4-3200, Samsung 990 EVO Plus NVMe, Windows 11 Pro, driver 616.92,
CUDA 12.8, Visual Studio 2022 Build Tools.

## What you need

| | |
| --- | --- |
| GPU | NVIDIA with 24 GB (other cards: set `CUDA_ARCH`, untested) |
| RAM | 128 GB for the 72 GiB arena in the config. Lower `--arena-gib` on smaller machines |
| Disk | ~370 GB free on an NVMe (NTFS): the model (148.1 GB, plus room for its shards while merging) and the official Engram shards (203 GB) |
| Tools | Visual Studio 2022 (C++ workload), CUDA Toolkit 12.8+, Git for Windows, Python 3.12 |

## 1. Clone with the engine

```bat
git clone --recurse-submodules https://github.com/vrami-dev/cenote D:\cenote
```

`engines\xolotl\` is Indras Mirror's [Xolotl](https://github.com/Indras-Mirror/Xolotl), pinned to a commit that includes the
Windows port. The config assumes `D:\cenote`; edit the paths if you clone somewhere else.

## 2. Build the engine

In Git Bash, then a normal command prompt:

```bash
cd /d/cenote/engines/xolotl && bash tools/xolotl/fetch-llama.sh
```

```bat
cd D:\cenote\engines\xolotl
python -m venv .venv-build
.venv-build\Scripts\pip install cmake ninja
build-win.bat configure
build-win.bat
```

Output: `engines\xolotl\build-win\ds41_generate.exe`. Build with nothing else heavy running: full-parallel nvcc can use a lot
of RAM, which is why `build-win.bat` defaults to 6 jobs.

## 3. Download the model

From `D:\cenote\engines\xolotl`:

```bat
rem lxe's dsx 2-bit build of DeepSeek-V4.1-Flash-1017 (148.1 GB in 4 shards) and its expert ranking
python tools\xolotl\win_fetch_files.py lxe/DeepSeek-V4.1-Flash-1017-dsx-2bit main D:\models\dsv41-1017-dsx ^
  SHA256SUMS config.json expert-rank.json ^
  DeepSeek-V4.1-Flash-1017-dsx-2bit-00001-of-00004.gguf DeepSeek-V4.1-Flash-1017-dsx-2bit-00002-of-00004.gguf ^
  DeepSeek-V4.1-Flash-1017-dsx-2bit-00003-of-00004.gguf DeepSeek-V4.1-Flash-1017-dsx-2bit-00004-of-00004.gguf

rem IndrasMirror's 1017 DSpark draft (Q2_K) and the tokenizer files, into the same folder
python tools\xolotl\win_fetch_files.py IndrasMirror/DeepSeek-V4.1-Flash-1017-XQ-Uncensored main D:\models\dsv41-1017-dsx ^
  V41-MTP-Vision-1017.Q2_K.gguf tokenizer/vocab.json tokenizer/merges.txt tokenizer/token_type.json tokenizer/chat_template.jinja

rem the official 1017 Engram shards, read in place
python tools\xolotl\win_fetch_files.py deepseek-ai/DeepSeek-V4.1-Flash-1017 main D:\models\dsv41-1017-engram ^
  config.json model.safetensors.index.json model-00047-of-00048.safetensors model-00048-of-00048.safetensors
```

Every file is checked against its Hugging Face sha256, and downloads resume.

## 4. Prepare the model

```bat
rem the expert tier reads one file: merge the 4 shards byte for byte
python tools\xolotl\gguf_merge_shards.py D:\models\dsv41-1017-dsx\DeepSeek-V4.1-Flash-1017-dsx-2bit-00001-of-00004.gguf ^
  D:\models\dsv41-1017-dsx\DeepSeek-V4.1-Flash-1017-dsx-2bit.gguf

rem the expert ranking in the format --rank reads
python ..\..\scripts\rank_json_to_bin.py D:\models\dsv41-1017-dsx\expert-rank.json D:\models\dsv41-1017-dsx\rank-dsx.bin
```

After the merge checks out you can delete the four shards (about 148 GB).

## 5. Serve

```bat
cd D:\cenote\engines\xolotl
python -m venv .venv-serve
.venv-serve\Scripts\pip install jinja2 regex
..\..\scripts\start-deepseek.cmd
```

- Ready in about a minute. Dashboard: http://127.0.0.1:8150. OpenAI-compatible API: http://127.0.0.1:8150/v1
  (Anthropic-style `/v1/messages` too).
- Model names: `deepseek-v4.1-flash-xolotl` (light routing, the default), `deepseek-v4.1-flash-xolotl-fast`,
  `deepseek-v4.1-flash-xolotl-exact`. See [the README](../README.md#deepseek-v41-flash-1017) for what each costs.
- Stop it with `python scripts\stop-all.py` (needs `pip install psutil`).
- One model at a time: the server pins 72 GiB of RAM and fills the GPU. Keep other RAM-heavy jobs off while it runs.

## Optional: build the 1017 draft yourself

IndrasMirror now publishes the 1017 draft, so this is only needed for other checkpoints. It is how the test rig built
its own before that upload existed, from the official 1017 shards 1, 2, 44, 45 and 46:

```bat
set V41_SRC=D:\models\dsv41-1017-src
.venv-serve\Scripts\python -I tools\v41\v41_sidecar.py --out D:\models\dsv41-1017-src\V41-MTP-Vision-1017.gguf
.venv-serve\Scripts\python -I tools\v41\v41_sidecar.py --verify D:\models\dsv41-1017-src\V41-MTP-Vision-1017.gguf --sample 4
build-win\v41_sidecar_requant.exe --in D:\models\dsv41-1017-src\V41-MTP-Vision-1017.gguf ^
  --out D:\models\dsv41-1017-src\V41-MTP-Vision-1017.Q2_K.gguf --type Q2_K
```

`v41_sidecar_requant.exe` is a single file compiled with `cl /O2 /EHsc /std:c++17 /MD` against the build's
`ggml-base`, `ggml-cpu` and `ggml` libraries. Run the requant with the server stopped: it needs about 12 GB of RAM.

## If something goes wrong

- **Every prompt over 96 tokens crashes (0xC0000374):** the engine was built without `GGML_CUDA_USE_GRAPHS` on
  `strata_mmq`. Rebuild from a current Xolotl (the fix is merged), or add `--no-chunk-mmq` to the config's `args`.
- **A long first prompt fails after several minutes with no error line:** under investigation. The server has a stall
  watchdog (`STRATA_ENGINE_STALL_S`, 90 s) that may end an engine that looks idle during a long GPU-only stretch. Try
  `STRATA_ENGINE_STALL_S=0` in the server's environment and report what you see.
- **It is slower than the README:** close video players and screen capture. On the test rig either one halved decode.
