# `server_profiles.py` — splitting the document into sections

**395 lines.** Named for the *profiles* document, but v5r uses it for the
*policy* document: the section-splitting machinery is shared, and only the table
readers differ.

## What v5r actually calls

| Function | Used for |
|---|---|
| `load_profiles(doc)` | splits a markdown document on `### <stem>` headings into `ServerProfile` objects |
| `profile_for(server, doc=...)` | finds the section whose fact line is ``**Tier: X** · `server-id` `` |
| `expected_use(text)` | pulls the "Expected organizational use" paragraph — the app purpose |

`server_policies.policy_for()` wraps `profile_for()` with the no-numbers guard, so
v5r never touches this module directly for anything but `expected_use`.

## What v5r does NOT call

`parse_asset_table()` and `parse_asset_rows()` read the profile document's
`| Asset | Sens. | C | I | A | Contents | Why |` inventory. They are how v4 and v5
got their sensitivity numbers. Pointed at a policy section they raise
`ProfileAssetTableError` — which is the intended failure: a policy has no such
table, so a profile-sensitivity mode cannot be aimed at one by accident.

`strip_profile_flags()`, `terse_profile()`, `prose_profile_view()` and
`structured_profile_view()` are the v3 description-scheme ablations (how much of
the written profile the model actually needs). Unused here.

## Why the fact line matters

Both documents key on ``**Tier: X** · `server-id` ``. That single convention is
what lets one parser serve an inventory-grade profile and a policy-grade
disclosure, and it is why the policy document's format notes call the heading and
the fact line "load-bearing".
