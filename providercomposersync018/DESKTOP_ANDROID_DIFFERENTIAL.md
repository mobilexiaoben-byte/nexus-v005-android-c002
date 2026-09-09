# V-005 C002 — Desktop/Android differential before 018

## Scope

Reference desktop: V-001 C003 extension 0.1.6.4, Claude real round-trip PASS and CLOSED.
Reference Android: V-005 C002 Claude TURN GENERATION DIAGNOSTIC 017, DEVICE PASS_DIAGNOSTIC with prompt still in composer and no materialized user turn/generation.

## Findings

1. Desktop `claude_provider.js` and Android 017 `claude_provider_c002.js` use the same core composer injection sequence: focus, native value setter for textarea/input or `document.execCommand('insertText')` for contenteditable, followed by input/change events.
2. Android ChatGPT already passes a complete round-trip while using the same isolated WebView bridge and essentially the same composer injection pattern. Therefore the Android WebView transport itself must not be replaced globally.
3. A material divergence exists in send-button discovery/readiness. Desktop prioritizes `button[data-testid="chat-input-send"]`; Android 016/017 introduced a scored near-composer fallback and only checked the DOM `disabled` property, not semantic states such as `aria-disabled`, `data-disabled`, `inert`, or CSS pointer-events.
4. DEVICE 017 proves that visible DOM text is not sufficient evidence of provider UI state synchronization: the prompt remained in the Claude composer and a manual send-arrow press was a no-op.
5. AndroidX WebKit deliberately supports isolated JavaScript worlds. Android `WebView.evaluateJavascript` evaluates JavaScript in the context of the currently displayed page. This gives a bounded diagnostic/fallback path to test whether the divergence is execution-world-specific without weakening the permanent isolated bridge.

## 018 design decision

018 keeps the isolated adapter and native WebMessage bridge as the default path. It adds a provider-neutral UI actuation protocol only when a semantically active send control is not observed after the normal isolated-world injection.

Protocol: `PROVIDER_UI_ACTUATE` / action `SET_COMPOSER_TEXT`.

The bundled provider adapter owns its composer/send selector contract. Native Android validates origin, bridge run correlation, request id, frozen-package binding, payload size, selector count/length, and action type. Native then performs one bounded page-context composer actuation and returns `PROVIDER_UI_ACTUATE_RESULT` to the isolated adapter. The adapter must then observe a semantically active send control before it may click. Otherwise it fails closed with `CLAUDE_COMPOSER_STATE_NOT_SYNCHRONIZED`.

## Multi-LLM constraint

The native protocol contains no Claude DOM selector and no Claude-specific actuation action. Provider-specific selectors remain in each signed/bundled adapter. The same protocol can therefore be reused by OpenAI, Anthropic, Gemini or later UI adapters while keeping provider-specific DOM knowledge outside the transport core.

018 remains SANDBOX/build validation only. DEVICE proof is a separate subsequent gate.
