# Unova A16 — FRLG source-only, original SHA-256

**Scope:** auxiliary non-native CI preparation only. This does not approve the Kanto native workflow, merge PR #195, or start A17. G=32/32, A=0/8, playable Unova=0/32, status=planned.

## Local evidence

The maintainer provided the original unmodified Essentials FRLG V1.1.rar in private conversation. Hashing its bytes directly (no extraction) produced SHA-256:

    48883c8217bcd9e7fa1b9446bddaa9db5f9715a7ba73ac02785b6660769e2683

This is exactly the pin in data/regions/kanto-source.json. The repacked ZIP is not a substitute for the original RAR. The original archive is NOT included in the repository, commits, releases, or CI artifacts.

## Fail-closed verifier

- tools/frlg_source_preflight.py validates original author/source/rights metadata and unchanged digest, checks RAR magic bytes and size limit, streams SHA-256, never extracts, persists, executes or uploads the archive.
- tests/test_frlg_source_preflight.py covers original pin, changed pin/source/author/rights, fake RAR, ZIP, quota HTML, malformed archive, oversized stream, symlink, missing secret, insecure/loopback URL, downgrade redirect and safe CLI behavior using synthetic bytes only.
- .github/workflows/frlg-source-only-preflight.yml runs offline tests on the helper branch. The network step is limited to a trusted workflow_dispatch with a short-lived signed HTTPS URL in GitHub Actions repository secret FRLG_SOURCE_URL. Without the secret, it fails closed. No URL is logged; download is checked in memory only.

## Authorized remote access path

1. Check permission with the rights holder before any hosting: the original manifest credits TheTinfoilTemplar and says DO NOT redistribute the archive. Valid possession does not imply redistribution consent.
2. If authorized, host the exact original RAR in maintainer-controlled private storage with a short-lived signed HTTPS URL; never commit it or publish it through GitHub Release/Artifacts.
3. Add the URL as GitHub repository Actions secret FRLG_SOURCE_URL (Settings / Secrets and variables / Actions). Do not paste it in issues, commits or workflow logs.
4. After this auxiliary workflow is available on the default branch, a trusted maintainer can manually run workflow_dispatch. This source-only verification is not yet a substitute for the old native pilot.
5. The existing Kanto native workflow remains required. Do not rerun it while Game.exe is prohibited: if the source is restored, it can execute the engine. Merge A16 only if every required workflow is genuinely green under approved execution conditions; only then begin A17.

No changes to original hashes or workflows, no false approvals of MapIDs, license, native engine or playable Unova.


## Rights review (official author resource, accessed 18 Nov 2026)

- Original author: TheTinfoilTemplar. The official Eevee Expo page at https://eeveeexpo.com/resources/1797/ states that Essentials FRLG may be used as a game template or that maps/events may be copied into another game. The author does **not** demand personal credit.
- Credits to the original Pokemon Essentials team are mandatory; credits to ENLS are required if using the pre-looped soundtrack. Related material includes RPG Maker XP and Pokemon rights belonging to third parties.
- The author's general usage permission does **not** explicitly establish permission to mirror/redistribute the complete RAR. The repository's pinned source manifest explicitly says "do not redistribute the archive, soundtrack or engine." **Keep that stricter policy**; require explicit rights-holder permission before re-hosting even privately for CI.
- Integrity evidence (same SHA-256) does not grant distribution rights, map ownership, game readiness, or authorization for native tests.

## Hardened CI integration

- A branch-only push/PR executes source metadata checks and synthetic tests without network access, archive, native engine, or secrets.
- A future manual `workflow_dispatch` must run on **main** after review/merge of the helper (GitHub requires a workflow_dispatch workflow on the default branch).
- Before manual dispatch, a maintainer must document explicit authorization and set repo Actions variable `FRLG_SOURCE_PERMISSION_CONFIRMED=true`; missing confirmation intentionally fails.
- Configure Actions secrets `FRLG_SOURCE_URL` (short-lived signed **direct** HTTPS URL) and `FRLG_SOURCE_HOST` (exact hostname of the approved private storage endpoint). Both must be configured by authorized maintainers. The verifier blocks local/private hosts, DNS-resolved private IPs, proxy use, and all redirects (prevents leaking signed query credentials to redirect hosts). URLs and secret values are not printed.
- The manual preflight streams and hashes RAR bytes without downloading them to disk. Source-only PASS does **not** turn the mandatory native Kanto workflow green; that workflow may run Game.exe and remains prohibited at this stage.
- Do not merge A16 PR #195 or start A17 until all relevant checks legitimately pass under the execution policy. Do not edit the pinned checksum or grant inferred rights.
