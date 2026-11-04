# Static scan: mcphunt_browser

Sensitivity of 9 assets, impact of 21 tools, blast radius of 189 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/browser/mcphunt_browser.json` (sha256 `3f7c6378600a`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/browser/mcphunt_browser.md` (classification section sha256 `111cd4e39e56`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:34:55+00:00 |

## For review

- ⚑ **Blast 5 without a word-for-word quote** (the prompt requires one; read the reason and decide whether it is really a 5): `browser_evaluate` → `public-web`, `browser_navigate` → `localhost-settings`, `browser_run_code` → `localhost-admin`, `browser_run_code` → `localhost-settings`, `browser_run_code` → `public-web`, `browser_drag` → `localhost-settings`
- 38 pair(s) the register does not list, rated by the model: `browser_close` → `localhost-admin` (1), `browser_close` → `localhost-settings` (1), `browser_close` → `localhost-index` (1), `browser_console_messages` → `localhost-admin` (5), `browser_console_messages` → `localhost-settings` (3), `browser_handle_dialog` → `localhost-admin` (5), `browser_handle_dialog` → `localhost-settings` (4), `browser_evaluate` → `localhost-admin` (5), `browser_evaluate` → `localhost-users` (5), `browser_evaluate` → `localhost-settings` (5), `browser_evaluate` → `public-web` (5), `browser_evaluate` → `page-traffic` (5), `browser_file_upload` → `localhost-admin` (5), `browser_fill_form` → `localhost-users` (5), `browser_press_key` → `localhost-users` (2), `browser_type` → `localhost-users` (5), `browser_navigate` → `page-traffic` (5), `browser_navigate_back` → `localhost-admin` (1), `browser_navigate_back` → `localhost-users` (2), `browser_navigate_back` → `localhost-settings` (2), `browser_navigate_back` → `localhost-index` (2), `browser_network_requests` → `localhost-admin` (5), `browser_network_requests` → `localhost-users` (5), `browser_network_requests` → `localhost-settings` (3), `browser_network_requests` → `localhost-index` (3), `browser_network_requests` → `public-web` (1), `browser_run_code` → `localhost-admin` (5), `browser_run_code` → `localhost-users` (5), `browser_run_code` → `localhost-settings` (5), `browser_run_code` → `localhost-index` (5), `browser_run_code` → `public-web` (5), `browser_run_code` → `page-traffic` (5), `browser_run_code` → `local-file-uploads` (5), `browser_drag` → `localhost-settings` (5), `browser_hover` → `localhost-users` (2), `browser_wait_for` → `localhost-settings` (2), `browser_wait_for` → `localhost-index` (1), `browser_wait_for` → `public-web` (1). Add them to the register, or confirm they are wrong.

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `localhost-admin` | 5 | Restricted | The admin panel contains the database password and the admin API token which are classified as Restricted according to the organization's policy. |
| `localhost-users` | 4 | Restricted | The asset holds each member's name, role and personal key, which are classified as Restricted according to the organization's policy. |
| `localhost-settings` | 3 | Confidential | The settings page is classified as Confidential because it changes internal settings and its exposure maps the internal estate. |
| `localhost-index` | 3 | Internal | The internal project dashboard holds status, last deploy and links which are meant to stay within the team according to the policy's data classification. |
| `public-web` | 1 | Public | According to the organization's description, public pages on the internet are classified as Public since they have no confidentiality left to lose. |
| `page-traffic` | 3 | Confidential | The asset 'page-traffic' includes network requests and console messages of the open page which can show tokens in headers and URLs, as per the policy's definition. This information is classified as Confidential because it exposes internal … |
| `page-scripts` | 4 | Restricted | According to the policy's asset register, `page-scripts` can read everything the page holds and send it anywhere, which is classified as Restricted due to its potential to expose sensitive information. |
| `local-file-uploads` | 4 | Restricted | Local files uploaded into a page's file field can carry sensitive information such as secrets or workspace data, which are classified as Restricted according to the policy. |
| `browser-session` | 2 | Routine | The browser's tabs, window, dialogs and waits with no page content are classified as Routine according to the organization's policy. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `browser_close` | 5 | write (rules unsure) | model | The tool 'browser_close' is described as closing a page, which aligns with the concept of removal or execution (no path back from inside the system). The destructive hint also corroborates this interpretation. |
| `browser_resize` | 2 | read (rules unsure) | model | The tool 'browser_resize' changes the dimensions of a browser window by setting its width and height parameters. This operation modifies the state of the browser window but does not involve reading or removing content, nor does it execute … |
| `browser_console_messages` | 3 | read (rules unsure) | model | The tool returns console messages which are considered content as they contain the substance of what is logged in the browser's console. The operation does not modify or remove any data, thus it falls under a CONTENT READ operation. |
| `browser_handle_dialog` | 4 | read (rules unsure) | model | The tool 'browser_handle_dialog' can accept or reject a dialog, which implies an action that could lead to further operations such as accepting a download, closing a warning, etc., thus it has the potential for significant impact. The para… |
| `browser_evaluate` | 5 | remove | rules | remove verbs: \beval(uate)?s?\b[^.]{0,20}\b(javascript/js/code/script/expression)\b; destructiveHint=true (hint only; does not raise the tier) |
| `browser_file_upload` | 4 | write (rules unsure) | model | The tool uploads one or multiple files based on the provided paths. This operation involves writing content to a destination, which aligns with an ordinary write operation as it allows for uploading entire files without any indication of b… |
| `browser_fill_form` | 4 | write (rules unsure) | model | The tool 'browser_fill_form' is described as filling multiple form fields, which implies writing content into those fields. The parameters include an array of fields to be filled in, indicating that the operation involves modifying the con… |
| `browser_press_key` | 2 | metadata | rules | metadata verbs: \bkeys?\b; destructiveHint=true (hint only; does not raise the tier) |
| `browser_type` | 4 | read (rules unsure) | model | The tool writes text into an editable element on a webpage, which constitutes an ordinary write operation as it modifies the content of the target element based on user input. |
| `browser_navigate` | 5 | read (rules unsure) | model | The tool 'browser_navigate' is described as navigating to a URL, which implies an action that could potentially execute code or commands on the target page, leading to various outcomes including but not limited to content modification or e… |
| `browser_navigate_back` | 3 | read | rules | read verbs: \bhistor(y/ies)\b; destructiveHint=true (hint only; does not raise the tier) |
| `browser_network_requests` | 3 | read (rules unsure) | model | The tool returns network requests data since the page was loaded, which includes metadata such as request headers and bodies if specified. It does not modify or remove any content; it only reads information. |
| `browser_run_code` | 5 | remove | rules | remove verbs: \brun (a )?(command/script/code/query/job)\b; destructiveHint=true (hint only; does not raise the tier) |
| `browser_take_screenshot` | 3 | read (rules unsure) | model | The tool takes a screenshot of the current page or an element within it and saves it to a file. This operation reads content from the browser viewport or specified element but does not modify any data, fitting the definition of CONTENT REA… |
| `browser_snapshot` | 3 | write (rules unsure) | model | The tool captures an accessibility snapshot of the current page and saves it to a markdown file or returns it in the response. This operation reads content from the browser and writes it to a file or returns it, which falls under CONTENT R… |
| `browser_click` | 4 | write (rules unsure) | model | The tool performs a click on a web page element which can lead to various actions such as submitting forms, navigating pages, or triggering JavaScript events that may result in content changes or data submission. The potential for these ac… |
| `browser_drag` | 5 | remove | rules | remove verbs: \bdrop\b; destructiveHint=true (hint only; does not raise the tier) |
| `browser_hover` | 1 | read (rules unsure) | model | The tool 'browser_hover' is described as hovering over an element on a page. Hovering typically does not result in any content modification or removal; it only involves interaction with the UI without changing state or data. The parameters… |
| `browser_select_option` | 3 | read | rules | read verbs: \bselect\b; bulk signal (array param or bulk wording); destructiveHint=true (hint only; does not raise the tier) |
| `browser_tabs` | 5 | write (rules unsure) | model | The tool can list tabs which is metadata retrieval (2), create a tab which involves writing content (4), and close or select a tab which could be seen as removal or modification of state (5). Given the ability to remove or modify state, th… |
| `browser_wait_for` | 1 | read (rules unsure) | model | The tool waits for text to appear or disappear or a specified time to pass without modifying any content or metadata. It only observes the state of the browser. |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `localhost-admin`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_close` | 1 | no | none | The tool 'browser_close' is destructive and can affect the asset by closing the admin panel, which contains sensitive information. |
| `browser_console_messages` | 5 | no | Q2: “the internal admin panel: the database password, the admin API token and the admin contact” | The tool can return console messages from the admin panel, which may contain sensitive information such as database passwords and API tokens. |
| `browser_handle_dialog` | 5 | no | Q2: “The admin panel's database password and API token” | The tool can handle a dialog that may appear on the admin panel, which is listed as an asset. |
| `browser_evaluate` | 5 | no | Q2: “The admin panel's database password and API token” | The tool can evaluate JavaScript expressions on the page, which could interact with elements of the admin panel. |
| `browser_file_upload` | 5 | no | Q2: “the database password, the admin API token and the admin contact (loss axis: C>I>A)” | The tool can upload files, and the asset includes sensitive data such as database password and admin API token which could be uploaded. |
| `browser_fill_form` | 5 | yes | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool is listed in the organization's register as reaching this asset. |
| `browser_press_key` | 5 | yes | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool browser_press_key is listed in the organization's register as reaching this asset. |
| `browser_type` | 5 | yes | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool 'browser_type' is listed in the organization's register as reaching this asset. |
| `browser_navigate` | 5 | yes | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool browser_navigate is listed in the organization's register as reaching this asset. |
| `browser_navigate_back` | 1 | no | none | The tool 'browser_navigate_back' can navigate back to the admin panel, which is listed as an asset that other tools like browser_click and browser_fill_form reach. |
| `browser_network_requests` | 5 | no | Q2: “the database password, the admin API token and the admin contact (loss axis: C>I>A)” | The tool can return network requests, which may include sensitive information such as database passwords and admin API tokens from the localhost-admin asset. |
| `browser_run_code` | 5 | no | Q2: “The admin panel's database password and API token are examples of Restricted data. Exposure of these values means they cannot be called back once sent out through a form, an upload or a script.” | The tool can execute arbitrary JavaScript code on the page, which includes interacting with elements that contain sensitive information such as database passwords and API tokens. |
| `browser_take_screenshot` | 5 | yes | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool is listed in the organization's register as reaching this asset. |
| `browser_snapshot` | 5 | yes | Q2: “the database password, the admin API token and the admin contact” | The tool is listed in the organization's register as reaching this asset. |
| `browser_click` | 5 | yes | Q2: “The admin panel's database password and API token” | The tool 'browser_click' is listed in the organization's register as reaching this asset, and its parameters allow interaction with elements on the admin panel. |
| `browser_select_option` | 5 | yes | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool is listed in the organization's register as reaching this asset. |

Not reached: `browser_resize`, `browser_drag`, `browser_hover`, `browser_tabs`, `browser_wait_for`

### `localhost-users`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_evaluate` | 5 | no | Q2: “each member's name, role and personal key” | The tool can evaluate JavaScript expressions on the page, which could be used to interact with and extract data from the team directory. |
| `browser_fill_form` | 5 | no | Q2: “The admin panel's database password and API token, the team directory's keys, an uploaded local file, a form or script that sends a secret out” | The tool 'browser_fill_form' can fill form fields, and the asset 'localhost-users' includes a team directory with each member's name, role, and personal key. Although the register does not list this specific tool for the asset, it is reaso… |
| `browser_press_key` | 2 | no | none | The tool can interact with the browser, and since it is listed as relevant for other assets that are similar in nature (e.g., `browser_click`), it can also affect this asset. |
| `browser_type` | 5 | no | Q2: “each member's name, role and personal key” | The tool 'browser_type' can interact with elements on the page, including those in the team directory. |
| `browser_navigate` | 5 | yes | Q2: “each member's name, role and personal key” | The tool browser_navigate is listed in the organization's register as reaching this asset. |
| `browser_navigate_back` | 2 | no | none | The tool 'browser_navigate_back' can navigate back to the team directory page, which is listed as an asset. |
| `browser_network_requests` | 5 | no | Q2: “each member's name, role and personal key” | The tool can capture network requests, which may include data from the team directory if accessed via a network request. |
| `browser_run_code` | 5 | no | Q2: “each member's name, role and personal key” | The tool can execute arbitrary JavaScript code on the page, which includes interacting with and extracting data from the team directory. |
| `browser_take_screenshot` | 5 | yes | Q2: “each member's name, role and personal key” | The tool is listed in the organization's register as reaching this asset. |
| `browser_snapshot` | 5 | yes | Q2: “each member's name, role and personal key” | The tool is listed in the organization's register as reaching this asset. |
| `browser_click` | 5 | yes | Q2: “each member's name, role and personal key” | The tool 'browser_click' is listed in the organization's register as reaching this asset, and its parameters allow interaction with elements on the page. |
| `browser_hover` | 2 | no | none | The tool 'browser_hover' can interact with elements on the page, including those in the team directory. |

Not reached: `browser_close`, `browser_resize`, `browser_console_messages`, `browser_handle_dialog`, `browser_file_upload`, `browser_drag`, `browser_select_option`, `browser_tabs`, `browser_wait_for`

### `localhost-settings`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_close` | 1 | no | none | The tool 'browser_close' can close the settings page, which is part of the localhost-settings asset. |
| `browser_console_messages` | 3 | no | Q2: “Exposure maps the internal estate or the people who run it; an action changes internal settings” | The tool retrieves console messages, which can include sensitive information from the settings page. |
| `browser_handle_dialog` | 4 | no | Q2: “A form filled on it is Restricted when it carries a secret value. Scripts and uploads rank as high as the most sensitive thing they can reach.” | The tool can handle a dialog that may appear on the settings page, which is listed as an asset. |
| `browser_evaluate` | 5 | no | Q2: “the internal settings page, whose form changes the service's settings” | The tool can evaluate JavaScript expressions on the page, which could interact with and modify settings. |
| `browser_fill_form` | 5 | yes | Q2: “A leak opens a production system; data sent out through a form, an upload or a script cannot be called back” | The tool is listed in the organization's register as reaching this asset. |
| `browser_press_key` | 2 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_type` | 4 | yes | Q2: “A leak opens a production system; data sent out through a form, an upload or a script cannot be called back (The settings page, whose form changes the service's settings)” | The tool 'browser_type' is listed in the organization's register as reaching this asset, and it can type text into form fields on the settings page. |
| `browser_navigate` | 5 | yes | Q2: “the settings page, whose form changes the service's settings” | The tool is listed in the organization's register as reaching this asset. |
| `browser_navigate_back` | 2 | no | none | The tool 'browser_navigate_back' can navigate back to the settings page, which is covered by this asset. |
| `browser_network_requests` | 3 | no | Q2: “The settings page, whose form changes the service's settings (loss axis: I>C>A)” | The tool 'browser_network_requests' can capture network requests from the settings page, which is listed as an asset that this tool can reach according to the organization's register. |
| `browser_run_code` | 5 | no | Q2: “A script run inside the open page: they can read everything the page holds and send it anywhere” | The tool can execute arbitrary Playwright code, which includes the ability to interact with forms and settings on the page. The asset description lists several tools that are relevant for interacting with this form, indicating that running… |
| `browser_take_screenshot` | 3 | yes | Q2: “The settings page, whose form changes the service's settings” | The tool is listed in the organization's register as reaching this asset. |
| `browser_snapshot` | 3 | yes | Q2: “The settings page, whose form changes the service's settings” | The tool is listed in the organization's register as reaching this asset. |
| `browser_click` | 4 | yes | Q2: “Exposure maps the internal estate or the people who run it; an action changes internal settings” | The tool is listed in the organization's register as reaching this asset. |
| `browser_drag` | 5 | no | Q2: “A form filled on it is Restricted when it carries a secret value. Scripts and uploads rank as high as the most sensitive thing they can reach.” | The tool 'browser_drag' can interact with elements on the settings page, which is listed as an asset that can be reached by other tools like 'browser_click', indicating it can also be affected by this tool. |
| `browser_select_option` | 4 | yes | Q2: “A leak opens a production system; data sent out through a form, an upload or a script cannot be called back” | The tool is listed in the organization's register as reaching this asset. |
| `browser_wait_for` | 2 | no | none | The tool can wait for specific conditions on the settings page, which is listed as an asset that this tool can reach according to the organization's register. |

Not reached: `browser_resize`, `browser_file_upload`, `browser_hover`, `browser_tabs`

### `localhost-index`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_close` | 1 | no | none | The tool 'browser_close' can close the page, which is part of the project dashboard asset. |
| `browser_navigate` | 5 | yes | Q2: “The settings page, the team directory's names and roles, network requests and console messages of internal pages” | The tool 'browser_navigate' is listed in the organization's register as reaching this asset. |
| `browser_navigate_back` | 2 | no | none | The tool 'browser_navigate_back' can affect the asset 'localhost-index', as it allows navigation to previous pages, which could include the project dashboard. |
| `browser_network_requests` | 3 | no | Q2 | The tool 'browser_network_requests' can capture network requests from the project dashboard, which is covered by the asset 'localhost-index'. The organization's register lists tools that interact with this asset, and while 'browser_network… |
| `browser_run_code` | 5 | no | Q2: “Scripts run inside the open page: they can read everything the page holds and send it anywhere” | The tool can execute arbitrary JavaScript code on the page, which could interact with and modify the project dashboard. |
| `browser_take_screenshot` | 2 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_snapshot` | 2 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_click` | 2 | yes | none | The tool 'browser_click' is listed in the organization's register as reaching this asset, and its parameters allow interaction with elements on the page. |
| `browser_wait_for` | 1 | no | none | The tool 'browser_wait_for' can be used to wait for specific conditions on the page, which is relevant to interacting with the project dashboard. |

Not reached: `browser_resize`, `browser_console_messages`, `browser_handle_dialog`, `browser_evaluate`, `browser_file_upload`, `browser_fill_form`, `browser_press_key`, `browser_type`, `browser_drag`, `browser_hover`, `browser_select_option`, `browser_tabs`

### `public-web`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_evaluate` | 5 | no | Q2 | The tool can evaluate JavaScript expressions on public pages, which are part of the 'public-web' asset. |
| `browser_fill_form` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_press_key` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_type` | 1 | yes | none | The tool 'browser_type' is listed in the organization's register as reaching this asset, and it can type text into editable elements on public web pages. |
| `browser_navigate` | 1 | yes | none | The tool 'browser_navigate' is listed in the organization's register as reaching this asset. |
| `browser_navigate_back` | 1 | yes | none | The tool 'browser_navigate_back' is listed in the organization's register as reaching this asset, and it operates on public pages which are part of the internet. |
| `browser_network_requests` | 1 | no | none | The tool 'browser_network_requests' can capture network requests from public pages on the internet, which is within the scope of the asset 'public-web'. The organization's register does not list this specific tool for the asset but it logi… |
| `browser_run_code` | 5 | no | Q2 | The tool can run arbitrary Playwright code snippets that interact with the page, which includes public web pages. |
| `browser_take_screenshot` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_snapshot` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_click` | 1 | yes | none | The tool 'browser_click' is listed in the organization's register as reaching this asset, and its parameters allow interaction with elements on public web pages. |
| `browser_drag` | 1 | yes | none | The tool 'browser_drag' is listed in the organization's register as reaching this asset, and its parameters indicate it can interact with elements on public web pages. |
| `browser_hover` | 1 | yes | none | The tool 'browser_hover' is listed in the organization's register as reaching this asset, and it operates on elements of public web pages. |
| `browser_select_option` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_wait_for` | 1 | no | none | The tool 'browser_wait_for' can be used to wait for certain conditions on public web pages, which are part of the 'public-web' asset. |

Not reached: `browser_close`, `browser_resize`, `browser_console_messages`, `browser_handle_dialog`, `browser_file_upload`, `browser_tabs`

### `page-traffic`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_console_messages` | 3 | yes | Q2: “"which can show tokens in headers and URLs"” | The tool browser_console_messages is listed in the organization's register as reaching this asset, and it directly returns console messages which are part of the page-traffic asset. |
| `browser_evaluate` | 5 | no | Q2: “The network requests and console messages of the open page, which can show tokens in headers and URLs” | The tool can evaluate JavaScript expressions on the page, which could potentially access and manipulate network requests and console messages. |
| `browser_navigate` | 5 | no | Q2: “The network requests and console messages of the open page, which can show tokens in headers and URLs” | The tool 'browser_navigate' can navigate to URLs that generate network requests and console messages, which are covered by the asset 'page-traffic'. Although the organization's register does not list this tool as reaching the asset, it is … |
| `browser_network_requests` | 3 | yes | Q2: “The network requests and console messages of the open page, which can show tokens in headers and URLs” | The tool 'browser_network_requests' is listed in the organization's register as reaching this asset, and its description matches the content of 'page-traffic'. |
| `browser_run_code` | 5 | no | Q2: “The network requests and console messages of the open page, which can show tokens in headers and URLs” | The tool can run arbitrary code that interacts with the page, which includes accessing network requests and console messages. |

Not reached: `browser_close`, `browser_resize`, `browser_handle_dialog`, `browser_file_upload`, `browser_fill_form`, `browser_press_key`, `browser_type`, `browser_navigate_back`, `browser_take_screenshot`, `browser_snapshot`, `browser_click`, `browser_drag`, `browser_hover`, `browser_select_option`, `browser_tabs`, `browser_wait_for`

### `page-scripts`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_evaluate` | 5 | yes | Q2: “Scripts run inside the open page: they can read everything the page holds and send it anywhere (loss axis: C>I>A)” | The tool 'browser_evaluate' is listed in the organization's register as reaching this asset, and its description indicates it can evaluate JavaScript expressions on a page or element, which aligns with the asset's definition of scripts run… |
| `browser_run_code` | 5 | yes | Q2: “Scripts run inside the open page: they can read everything the page holds and send it anywhere” | The tool is listed in the organization's register as reaching this asset. |

Not reached: `browser_close`, `browser_resize`, `browser_console_messages`, `browser_handle_dialog`, `browser_file_upload`, `browser_fill_form`, `browser_press_key`, `browser_type`, `browser_navigate`, `browser_navigate_back`, `browser_network_requests`, `browser_take_screenshot`, `browser_snapshot`, `browser_click`, `browser_drag`, `browser_hover`, `browser_select_option`, `browser_tabs`, `browser_wait_for`

### `local-file-uploads`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_file_upload` | 4 | yes | Q2: “Local files the browser uploads into a page's file field (loss axis: C>I>A)” | The tool is listed in the organization's register as reaching this asset. |
| `browser_run_code` | 5 | no | Q2: “Local files the browser uploads into a page's file field (loss axis: C>I>A)” | The tool can execute JavaScript code that interacts with the page, including uploading local files into a file field. |

Not reached: `browser_close`, `browser_resize`, `browser_console_messages`, `browser_handle_dialog`, `browser_evaluate`, `browser_fill_form`, `browser_press_key`, `browser_type`, `browser_navigate`, `browser_navigate_back`, `browser_network_requests`, `browser_take_screenshot`, `browser_snapshot`, `browser_click`, `browser_drag`, `browser_hover`, `browser_select_option`, `browser_tabs`, `browser_wait_for`

### `browser-session`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `browser_close` | 1 | yes | none | The tool 'browser_close' is listed in the organization's register as reaching this asset, and it directly operates on the browser session. |
| `browser_resize` | 1 | yes | none | The tool browser_resize is listed in the organization's register as reaching this asset, and it operates on the browser window which is part of the browser session. |
| `browser_handle_dialog` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |
| `browser_navigate_back` | 1 | yes | none | The tool 'browser_navigate_back' is listed in the organization's register as reaching this asset, and it operates on the browser session by navigating back to a previous page. |
| `browser_tabs` | 1 | yes | none | The tool browser_tabs operates on the browser's tabs, which is part of the browser-session asset. |
| `browser_wait_for` | 1 | yes | none | The tool is listed in the organization's register as reaching this asset. |

Not reached: `browser_console_messages`, `browser_evaluate`, `browser_file_upload`, `browser_fill_form`, `browser_press_key`, `browser_type`, `browser_navigate`, `browser_network_requests`, `browser_run_code`, `browser_take_screenshot`, `browser_snapshot`, `browser_click`, `browser_drag`, `browser_hover`, `browser_select_option`
