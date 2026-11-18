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
