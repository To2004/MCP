# Bot Day Check web page

The participant page for the human study of the dynamic layer. It shows the public item bank
(`../items.json`) only, never the key, and is published as a private claude.ai artifact.

## Files

| File | What it is |
|---|---|
| `index.template.html` | the page: screens, layout and saving. `__BANK_JSON__` marks where the bank goes |
| `index.html` | the built page: the template with `items.json` embedded. Do not edit by hand |

Build it from the repository root after every change to the template or the bank:

```bash
uv run python reports/experiments/dynamic_dimensions/human_study/build_page.py
uv run pytest tests/test_dynamic_human_web.py -q
```

`build_page.py` refuses a bank that carries a key-only field (`stratum`, `listed`, `strongest`,
...), and a test checks that the committed `index.html` matches the template and the bank.

## Published page

- Link: <https://claude.ai/artifact/6E1zsZfiQPzAq8jkDkBFDn> (bank `dyn-human-v1`, published
  2026-10-25). Republish to the same link from the conversation that published it, or pass the
  link as `url` from a new one.
- Capabilities: `db` with two rules (`responses` read and write by the owner only;
  `responses/{self}` read and write by the viewer it belongs to) and `user` (an opaque viewer
  id, no name or email).

## Sharing it, and how answers come back

The page is private until the owner shares it from its Share menu. Who can save answers to the
store depends on how a person opens it:

| Who opens it | Answers reach the store? | What to do |
|---|---|---|
| The owner (for example, running the study in person on one device) | yes; each person is one run inside the owner's document | press "Start again for another person" between people |
| Someone invited by email as an Editor (only while the page has no public link) | yes | nothing |
| A member of the owner's Team or Enterprise organisation with Contributor access or more | yes | nothing |
| Anyone else, including everyone who opens a public link | no | they copy the answer code from the last screen and send it to you |

The page tells each person which case applies ("Answers saved" or "you will get an answer code
at the end"). Paste the codes you receive into a text file, as many per file as you like.

Answers are kept on the person's device while they work, so a reload or a break resumes where
they stopped. The page asks no name or contact details.

## Reading the answers

1. Export the store's `responses` collection (as the owner, with the `ArtifactData` tool, action
   `list`, collection `responses`, `out_dir` set to a folder) and save it as JSON.
2. Gather everything into one list:

   ```bash
   uv run python reports/experiments/dynamic_dimensions/human_study/collect_responses.py \
       --store store_export.json --codes codes.txt \
       --claude reports/experiments/dynamic_dimensions/human_study/claude_ratings.json \
       --out responses.json
   ```

3. Run the analysis as described in [../README.md](../README.md#analysis).

## Before sharing

Ethics approval and the consent text are the study owner's responsibility (see
[../README.md](../README.md#before-anyone-takes-the-survey)). The welcome screen says the study
takes about 30 minutes, is voluntary, can be stopped at any time, stores no name, and shows
simulated agents only. Change that text in `index.template.html` if the ethics committee asks
for different wording, then rebuild and republish.
