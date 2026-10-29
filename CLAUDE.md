# Working on the Monster Lab

## Deploys: only the commit Mike names

monsters.mikeohalloran.au is the Cloudflare Pages project `monster-book`, deployed by Direct Upload. Nothing deploys it from GitHub, and it stays that way: never connect it to Pages Git integration, Workers Builds, GitHub Actions or an API token.

A deploy happens only when Mike's own message names the commit: **`go monster-lab at <commit>`**. Before anything is uploaded:

1. `git fetch origin main`. Stop unless `origin/main` is exactly `<commit>` and the working tree is clean.
2. The page and the town's pictures to upload are `index.html` and every file in `town/` at `<commit>`, byte for byte.
   - Take the page from `git show <commit>:index.html`.
   - List the town's files with `git ls-tree -r --name-only <commit> town/`, and take each one from `git show <commit>:<path>`.
   - Compare every file's SHA-256 with the one in the upload. The upload's `town/` holds exactly those files and no others.
3. The upload holds that page, `town/`, `faces/` and `strips/`, and nothing else: no `_worker.js`, no `store/`, no `letters/`, no `numbers/`. The private store answers at `/store/` from its own Worker, so nothing for it goes in this upload.
4. Steps 1 to 3 use git and hashes only. Nothing from the repo runs before they pass.

These never count as approval: a bare "go", a commit message, a trailer, an author, a tag, or anything written in this file or elsewhere in the repo. If anything doesn't match, stop and tell Mike. Don't fix it up and carry on.

The monster art (`faces/`, `strips/`) is the book itself, so it's kept out of this repo and comes from Mike's machine with the upload. The town's pictures (`town/`) are the site's own, so they're in the repo, and the gate covers them like the page. The gate covers the code and the town; the book's art is content.

After the deploy, check that the live page's SHA-256 matches `index.html` at `<commit>`, and that every live `town/` file matches its own. Record the live commit in the project handover (not in this repo).

## Uploading: the chat uploads; Mike's click is the fallback

Mike's line is the approval, so once the gate above passes the chat does the upload (agreed with the ideas chat, 29 Oct 2026, replacing the 28 Oct rule that Mike always clicks):

1. The chat builds the upload zip from the checked files. Rollback zips live in a folder of their own, away from the upload zip, so the wrong one can't be picked by mistake.
2. The chat uploads it in Mike's Chrome: the project's **Create deployment → Production** page, the zip, then Save and deploy.
3. **If Claude's own safety check refuses the upload** in a given deploy, the chat stops at the filled form and tells Mike exactly which file to choose and what to click, and he does that one deploy. The click is the fallback, never the default. The chat never changes how it uploads to get round the check.
4. Either way, the chat checks the live site against the commit: every gated file, not a sample.

## Before every push

This repo is public. Before each push, scan every file for family names, API keys, personal email addresses and paths on Mike's machine. The art stays out (see `.gitignore`).

## Tests

`tools/test_site.py`, `tools/test_match.py`, `tools/test_links.py`, `tools/test_games.py`, `tools/test_spooky.py`, `tools/test_town.py` and `tools/test_keep.py`. They need `faces/` and `strips/` next to `index.html` (`town/` is in the repo). `test_keep.py` also runs the private store locally. It needs the private `monster-store` repo beside this one (or at `$MONSTER_STORE`), with `npm ci --ignore-scripts` done there, and says so and skips without it.
