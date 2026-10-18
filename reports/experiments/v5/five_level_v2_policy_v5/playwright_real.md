# Scan — playwright:real

_kind=playwright · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5 · bands={'low': 9, 'medium': 28, 'high': 11, 'critical': 5, 'na': 187}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = LLM classification against the org POLICY (classify -> map; the org supplies no numbers)
- tool impact = deterministic ladder (static_impact.py); the v4 impact prompt decides only where the ladder abstains (confidence < 0.5)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: browser automation
- **asset_meaning**: data and state managed by the browser during automated testing or RPA tasks against internal web applications
- **blast_radius_meaning**: the extent to which a tool can affect the data, state, or behavior of the browser session and its underlying processes
- **dangerous_classes**: holds credentials or tokens, contains sensitive page content behind an authenticated login, triggers real actions in loaded applications
- **irreversible_actions**: browser_run_code_unsafe
- **worked_example**: The tool 'browser_click' on asset 'page-interactive-state' can trigger irreversible actions like approving or deleting items within the application, making it highly impactful.

## Tool impact

| tool | impact |
| --- | --- |
| `browser_close` | 4 |
| `browser_resize` | 4 |
| `browser_console_messages` | 3 |
| `browser_handle_dialog` | 5 |
| `browser_evaluate` | 5 |
| `browser_file_upload` | 4 |
| `browser_drop` | 5 |
| `browser_find` | 3 |
| `browser_fill_form` | 4 |
| `browser_press_key` | 2 |
| `browser_type` | 5 |
| `browser_navigate` | 5 |
| `browser_navigate_back` | 3 |
| `browser_network_requests` | 3 |
| `browser_network_request` | 3 |
| `browser_run_code_unsafe` | 5 |
| `browser_take_screenshot` | 3 |
| `browser_snapshot` | 3 |
| `browser_click` | 4 |
| `browser_drag` | 5 |
| `browser_hover` | 1 |
| `browser_select_option` | 3 |
| `browser_tabs` | 4 |
| `browser_wait_for` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `server-process-execution` | 5 |
| `authenticated-session-state` | 5 |
| `network-traffic-content` | 4 |
| `internal-page-content` | 3 |
| `local-file-contents` | 3 |
| `form-input-and-credentials` | 4 |
| `page-interactive-state` | 3 |
| `console-and-debug-output` | 3 |
| `navigation-history` | 3 |
| `browser-runtime-state` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | browser_close | browser_resize | browser_console_messages | browser_handle_dialog | browser_evaluate | browser_file_upload | browser_drop | browser_find | browser_fill_form | browser_press_key | browser_type | browser_navigate | browser_navigate_back | browser_network_requests | browser_network_request | browser_run_code_unsafe | browser_take_screenshot | browser_snapshot | browser_click | browser_drag | browser_hover | browser_select_option | browser_tabs | browser_wait_for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `server-process-execution` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (5×5×5) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `authenticated-session-state` | N/A | N/A | N/A | N/A | 100 (5×4×5) 🔴 | N/A | N/A | N/A | 80 (5×4×4) 🟠 | N/A | 100 (5×4×5) 🔴 | 100 (5×4×5) 🔴 | N/A | N/A | N/A | 125 (5×5×5) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `network-traffic-content` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 60 (4×3×5) 🟡 | N/A | 60 (4×5×3) 🟡 | 12 (4×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `internal-page-content` | 24 (3×2×4) 🟢 | N/A | N/A | 45 (3×3×5) 🟡 | 60 (3×4×5) 🟡 | N/A | 45 (3×3×5) 🟡 | 27 (3×3×3) 🟢 | 36 (3×3×4) 🟡 | 18 (3×3×2) 🟢 | 45 (3×3×5) 🟡 | 60 (3×4×5) 🟡 | 27 (3×3×3) 🟢 | N/A | N/A | N/A | 36 (3×4×3) 🟡 | 36 (3×4×3) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | 3 (3×1×1) 🟢 | 18 (3×2×3) 🟢 | N/A | 6 (3×1×2) 🟢 |
| `local-file-contents` | N/A | N/A | N/A | N/A | N/A | 48 (3×4×4) 🟡 | 60 (3×4×5) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `form-input-and-credentials` | N/A | N/A | N/A | N/A | 60 (4×3×5) 🟡 | N/A | 60 (4×3×5) 🟡 | N/A | 48 (4×3×4) 🟡 | 24 (4×3×2) 🟢 | 60 (4×3×5) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 36 (4×3×3) 🟡 | N/A | N/A |
| `page-interactive-state` | N/A | N/A | N/A | 60 (3×4×5) 🟡 | 45 (3×3×5) 🟡 | N/A | 45 (3×3×5) 🟡 | N/A | 36 (3×3×4) 🟡 | 18 (3×3×2) 🟢 | 60 (3×4×5) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 48 (3×4×4) 🟡 | 45 (3×3×5) 🟡 | 3 (3×1×1) 🟢 | 27 (3×3×3) 🟢 | N/A | N/A |
| `console-and-debug-output` | N/A | N/A | 36 (3×4×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `navigation-history` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 45 (3×3×5) 🟡 | 9 (3×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 36 (3×3×4) 🟡 | N/A |
| `browser-runtime-state` | 16 (2×2×4) 🟢 | 16 (2×2×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 30 (2×3×5) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | 4 (2×1×2) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | browser_close | browser_resize | browser_console_messages | browser_handle_dialog | browser_evaluate | browser_file_upload | browser_drop | browser_find | browser_fill_form | browser_press_key | browser_type | browser_navigate | browser_navigate_back | browser_network_requests | browser_network_request | browser_run_code_unsafe | browser_take_screenshot | browser_snapshot | browser_click | browser_drag | browser_hover | browser_select_option | browser_tabs | browser_wait_for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `server-process-execution` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `authenticated-session-state` | N/A | N/A | N/A | N/A | 4 | N/A | N/A | N/A | 4 | N/A | 4 | 4 | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `network-traffic-content` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | 5 | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `internal-page-content` | 2 | N/A | N/A | 3 | 4 | N/A | 3 | 3 | 3 | 3 | 3 | 4 | 3 | N/A | N/A | N/A | 4 | 4 | 2 | 3 | 1 | 2 | N/A | 1 |
| `local-file-contents` | N/A | N/A | N/A | N/A | N/A | 4 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `form-input-and-credentials` | N/A | N/A | N/A | N/A | 3 | N/A | 3 | N/A | 3 | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A |
| `page-interactive-state` | N/A | N/A | N/A | 4 | 3 | N/A | 3 | N/A | 3 | 3 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 3 | 1 | 3 | N/A | N/A |
| `console-and-debug-output` | N/A | N/A | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `navigation-history` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A |
| `browser-runtime-state` | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 1 |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `browser_close` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_resize` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_console_messages` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `browser_handle_dialog` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_evaluate` | **EXECUTE** | 5 (Critical) | EXECUTE | verb-fallback |
| `browser_file_upload` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `browser_drop` | **DELETE** | 5 (Critical) | DELETE | verb-fallback |
| `browser_find` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |
| `browser_fill_form` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_press_key` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_type` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_navigate` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_navigate_back` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_network_requests` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_network_request` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_run_code_unsafe` | **EXECUTE** | 5 (Critical) | EXECUTE | rules |
| `browser_take_screenshot` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_snapshot` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_click` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_drag` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_hover` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_select_option` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_tabs` | **READ** | 2 (Low) | READ | verb-fallback |
| `browser_wait_for` | **READ** | 2 (Low) | READ | verb-fallback |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `browser_resize` | `width` | 2 | — | controls window size, not inherently risky |
| `browser_resize` | `height` | 2 | — | controls window size, not inherently risky |
| `browser_console_messages` | `filename` | 4 | — | allows writing to arbitrary files, potentially leading to fi |
| `browser_console_messages` | `all` | 3 | — | potentially exposes all session messages, widening data expo |
| `browser_console_messages` | `level` | 2 | — | limits the scope to message severity |
| `browser_handle_dialog` | `promptText` | 4 | — | potentially misleading or malicious text |
| `browser_handle_dialog` | `accept` | 2 | — | binary flag, limited impact |
| `browser_evaluate` | `function` | 5 | — | fully controllable code execution on the server |
| `browser_evaluate` | `element` | 3 | — | can be used to target specific elements for malicious action |
| `browser_evaluate` | `target` | 2 | — | identifies the element but is less flexible than 'function' |
| `browser_evaluate` | `filename` | 1 | — | only specifies where to save results, no direct risk amplifi |
| `browser_file_upload` | `paths` | 4 | >= 10 files | allows bulk upload, potentially for flooding or malicious fi |
| `browser_drop` | `data` | 5 | — | fully controlled MIME-typed data, potentially malicious cont |
| `browser_drop` | `paths` | 4 | — | fully controlled payload that can introduce arbitrary files |
| `browser_drop` | `element` | 2 | — | merely names the target |
| `browser_drop` | `target` | 1 | — | names the exact element or selector, no amplification |
| `browser_find` | `regex` | 4 | — | potentially complex and powerful pattern matching |
| `browser_find` | `text` | 2 | — | controlled text input with limited impact |
| `browser_fill_form` | `fields` | 4 | >= 10 fields | can be used to send bulk data or exploit form field vulnerab |
| `browser_press_key` | `key` | 3 | — | can simulate harmful keyboard inputs |
| `browser_type` | `text` | 5 | — | fully controlled payload, can inject malicious content |
| `browser_type` | `submit` | 4 | — | can trigger unintended form submissions or actions |
| `browser_type` | `target` | 3 | — | can be manipulated to target unintended elements |
| `browser_type` | `slowly` | 3 | — | may enable evasion of rate-limiting protections |
| `browser_type` | `element` | 2 | — | merely names the target |
| `browser_navigate` | `url` | 4 | — | can be used to navigate to malicious sites |
| `browser_network_requests` | `filter` | 4 | — | allows regex-based filtering, potentially broadening scope |
| `browser_network_requests` | `static` | 2 | — | controls inclusion of static resources, limited scope |
| `browser_network_requests` | `filename` | 1 | — | specifies output file name, minimal risk |
| `browser_network_request` | `filename` | 4 | — | allows saving data, potentially leaking sensitive informatio |
| `browser_network_request` | `part` | 3 | — | can be used to focus on sensitive parts of requests |
| `browser_network_request` | `index` | 2 | — | merely names the target request |
| `browser_run_code_unsafe` | `code` | 5 | — | arbitrary JavaScript execution |
| `browser_run_code_unsafe` | `filename` | 4 | — | loads arbitrary code from a file |
| `browser_take_screenshot` | `fullPage` | 4 | true | widens scope to full page, potentially more data exposure |
| `browser_take_screenshot` | `filename` | 3 | — | can influence file system operations |
| `browser_take_screenshot` | `scale` | 2 | — | affects image resolution but not security directly |
| `browser_take_screenshot` | `element` | 2 | — | merely names the target |
| `browser_take_screenshot` | `type` | 2 | — | image format control, limited impact |
| `browser_take_screenshot` | `target` | 1 | — | specific element selector, low risk |
| `browser_snapshot` | `depth` | 4 | >= 10 | increases the scope of data captured, potentially overwhelmi |
| `browser_snapshot` | `filename` | 3 | — | can write to arbitrary file paths, potential for abuse |
| `browser_snapshot` | `target` | 2 | — | names the target element, limited control |
| `browser_snapshot` | `boxes` | 2 | — | includes bounding box information, limited risk |
| `browser_click` | `modifiers` | 4 | — | can change the action's effect significantly with key combin |
| `browser_click` | `target` | 3 | — | can target any element on the page, potentially sensitive on |
| `browser_click` | `element` | 2 | — | merely descriptive, not directly executable |
| `browser_click` | `doubleClick` | 1 | — | affects click behavior but not scope or magnitude |
| `browser_click` | `button` | 1 | — | limits to mouse button, no amplification of risk |
| `browser_drag` | `startTarget` | 4 | — | exact target reference or selector, high control over intera |
| `browser_drag` | `endTarget` | 4 | — | exact target reference or selector, high control over intera |
| `browser_drag` | `startElement` | 2 | — | human-readable description, low risk |
| `browser_drag` | `endElement` | 2 | — | human-readable description, low risk |
| `browser_hover` | `target` | 3 | — | can target any element on the page, moderate risk |
| `browser_hover` | `element` | 2 | — | human-readable description, low risk |
| `browser_select_option` | `values` | 4 | >= 20 values | can control multiple selections, potentially leading to bulk |
| `browser_select_option` | `element` | 2 | — | merely names the target |
| `browser_select_option` | `target` | 1 | — | names the specific element to interact with |
| `browser_tabs` | `url` | 5 | — | fully controllable input that can navigate to any URL |
| `browser_tabs` | `action` | 3 | — | defines the operation but is limited to predefined actions |
| `browser_tabs` | `index` | 2 | — | only specifies a tab index, limiting scope |
| `browser_wait_for` | `time` | 3 | >= 60 | Can cause excessive waiting, potentially leading to server t |
| `browser_wait_for` | `text` | 2 | — | Limited risk as it only specifies text content to wait for |
| `browser_wait_for` | `textGone` | 2 | — | Similar to 'text', but waits for disappearance; limited risk |
