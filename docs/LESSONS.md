# Lessons from the rig

What running three frontier-size open models on one 24 GB card under Windows taught us. Each one is backed by a run in
[BENCHMARKS.md](BENCHMARKS.md) or a merged change.

## The Windows port

1. **The worst bug was a linker detail.** Every DeepSeek prompt over 96 tokens corrupted the heap (0xC0000374). Two
   libraries compiled the same MMQ host templates with different `GGML_CUDA_USE_GRAPHS` settings, so the
   `ggml_backend_cuda_context` layouts differed, and MSVC's linker kept the first library's instances. GNU ld keeps the
   other copy, which is why Linux never saw it. Fix: define it on `strata_mmq` too (Xolotl #10).
2. **Decode on Windows is launch-bound.** With CUDA graphs off, DeepSeek's attention + router step goes from 23.4 to 47.4
   ms per token. The expert tier is not graphed yet. Its own profile puts launches at about 5 ms of a ~47 ms step, so
   graphing it is worth roughly +10-15%, not more. (We first guessed +30-60% before reading our own profile.)
3. **Prompt reading is I/O-bound.** During a 78K-token DeepSeek prompt the GPU sat around 6% busy while experts streamed
   over PCIe and from the SSD.
4. **Large pages don't matter for the copies.** Plain 4 KB pinned memory already moves 26 GB/s host to GPU on this board.
5. **Shards can be merged without decoding the types.** The expert tier reads one file; tensor lengths come from the
   shard offsets, so a byte-for-byte merge works even for quant types llama.cpp can't size.

## Measuring

6. **The PC is the noise.** A video player or screen capture halved decode. One server per variant was too noisy; one
   server with the mode switched per request, in a rotation and its reverse, gave stable numbers.
7. **Build the meter first.** The route meter (expert picks swapped vs exact routing) caught a bug in our own toggle that
   the speed tests hid: a regenerated prompt kept the previous request's routing. Fixed before anything was pushed.
8. **"Fast mode" is not free.** The old fast default swapped 37% of DeepSeek's expert picks. The light nudge swaps 26%
   for 12% less speed, and keeps a real quality score close to exact routing.
9. **Characters matching the exact answer is useless as a quality signal.** One swapped token changes every word after it.
10. **Read the paper behind the trick.** colibri's cache-aware rule is the baseline in the paper it cites
    (arXiv:2412.00099); the paper's own method, a nudge scaled to each layer's score range, beat it. That is next here.

## Running three models on one box

11. **One model at a time.** DeepSeek pins 72 GiB, GLM about 93 GB, Swift about 59 GB. A requant job beside DeepSeek
    dropped free RAM to 1.7 GB and slowed everything.
12. **Batch slots lose on this CPU.** Three agents on Strata finished 12-25% sooner on one slot than on three.
13. **Engine updates are real speed.** Strata 0.1.41 to 0.1.45: Swift code decode +33% at equal cache size. Maya 1.0.27
    to 1.1.15 with the S24 quant: GLM about 40% faster.
14. **Check the encoder.** DeepSeek's prompt encoder in the server was an older copy of DeepSeek's own; another
    project's docs pointed to the newer one. Synced in Xolotl #11.
15. **Privacy is a setting.** The DeepSeek server kept a plain-text copy of every answer in `%TEMP%`. A config `env` block
    only reaches the engine, so `STRATA_TEXT_LOG=0` has to be set where the server starts (the launchers do it).
