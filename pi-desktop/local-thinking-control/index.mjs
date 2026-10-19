// Explicit per-request reasoning for the cenote stack's local servers (Pi Desktop extension).
// Uses Pi's documented extension hook; does not change the application bundle.
import { appendFile } from 'node:fs/promises';
const expected = new Map([
  ['qwen3.8-flash-next-iq3_s', 'http://127.0.0.1:8080/v1'],
  ['swift-1.5-iq3_s', 'http://127.0.0.1:8080/v1'],   // Swift 1.5, the daily Flash model on Strata since 2026-10-10
  ['swift-1.5-uncensored-iq3_s', 'http://127.0.0.1:8080/v1'],   // SC117's abliterated Swift (Start Swift Uncensored, 2026-10-10)
  ['glm-5.3-flash', 'http://127.0.0.1:8090/v1'],   // local GLM-5.3-Flash on Project Maya (added 2026-10-09)
  ['deepseek-v4.1-flash-xolotl', 'http://127.0.0.1:8150/v1'],   // local DeepSeek-V4.1-Flash on Xolotl/cenote (added 2026-10-18)
  ['deepseek-v4.1-flash-xolotl-exact', 'http://127.0.0.1:8150/v1'],   // the same server, exact expert routing (quality mode)
  ['deepseek-v4.1-flash-xolotl-fast', 'http://127.0.0.1:8150/v1'],   // the same server, the stronger routing nudge (speed mode)
]);
// Qwen-family templates know low / medium / xhigh; GLM-5.3 knows low / high / max (Maya: none = thinking off);
// DeepSeek-V4.1's server (serve_ds41.py) maps none / low / medium / high / max to effort 0 / 50 / 62 / 75 / 100.
const levels = { off: 'none', minimal: 'low', low: 'low', medium: 'medium', high: 'xhigh', xhigh: 'xhigh', max: 'xhigh' };
const glmLevels = { off: 'none', minimal: 'low', low: 'low', medium: 'high', high: 'high', xhigh: 'max', max: 'max' };
const dsLevels = { off: 'none', minimal: 'low', low: 'low', medium: 'medium', high: 'high', xhigh: 'max', max: 'max' };
const levelMaps = { 'glm-5.3-flash': glmLevels, 'deepseek-v4.1-flash-xolotl': dsLevels, 'deepseek-v4.1-flash-xolotl-exact': dsLevels, 'deepseek-v4.1-flash-xolotl-fast': dsLevels };
export default function localThinkingControl(pi) {
  pi.on('before_provider_request', async (event, ctx) => {
    const model = ctx.model;
    const payload = event.payload;
    if (!model || !expected.has(model.id) || model.baseUrl?.replace(/\/$/, '') !== expected.get(model.id)) return;
    if (!payload || typeof payload !== 'object' || payload.model !== model.id) return;
    const selected = pi.getThinkingLevel();
    const effort = (levelMaps[model.id] || levels)[selected];
    if (!effort) throw new Error('Unsupported local thinking selection: ' + selected);
    const kwargs = { ...payload.chat_template_kwargs, enable_thinking: effort !== 'none' };
    if (effort === 'none') delete kwargs.reasoning_effort;
    else kwargs.reasoning_effort = effort;
    const updated = { ...payload, reasoning_effort: effort, chat_template_kwargs: kwargs };
    // Optional audit (LOCAL_THINKING_AUDIT=<file>): settings only, never prompts, responses, credentials or headers.
    if (process.env.LOCAL_THINKING_AUDIT) await appendFile(process.env.LOCAL_THINKING_AUDIT, JSON.stringify({ time: new Date().toISOString(), model: model.id, selected, reasoning_effort: effort, enable_thinking: kwargs.enable_thinking }) + '\n');
    return updated;
  });
}
