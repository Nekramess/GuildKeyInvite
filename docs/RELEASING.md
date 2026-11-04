# Releasing Guild Key Invite

Release file name standard: `GuildKeyInvite-v<Version>-forever.zip`, for example `GuildKeyInvite-v0.1.0-forever.zip`.

- `<Version>` is the `## Version:` line in `GuildKeyInvite/GuildKeyInvite.toc`. The display name ("Guild Key Invite") never goes in the file name.
- Build it only with `bash tools/release.sh` (calls `tools/package.sh`). Never zip by hand, rename, retype the name in CurseForge's upload form, or put the version first.
- Exactly one zip is stored in `releases/`. Download from `https://github.com/Nekramess/GuildKeyInvite/raw/main/releases/GuildKeyInvite-v0.1.0-forever.zip` once the PR is merged.
- One version, one file: bump `## Version` for every release, and never upload different contents under a version that is already on CurseForge.

CurseForge listing text, upload fields and changelog are in `curseforge/LISTING.md`; update it (and `CHANGELOG.md`) with every release.

## Libraries

The minimap button uses LibDBIcon-1.0 (v56), embedded in `GuildKeyInvite/Libs/` with LibStub, CallbackHandler-1.0 and LibDataBroker-1.1, and listed first in the `.toc`. Copies came from public GitHub (LibDataBroker from tekkub/libdatabroker-1-1, the rest from Questie, 4 Nov 2026). Never hand-build a minimap button.

## Steps

1. Branch off `main` (never commit to `main`), change the code, bump `## Version` once per release.
2. `python3 tests/gki_test.py` and `python3 tests/mutation_check.py` (needs `pip install lupa`).
3. `bash tools/release.sh` so `releases/` holds the zip for the new version.
4. Open a PR; merge; upload the zip from `releases/` to CurseForge exactly as built.
5. Update the version table in the project overview.
