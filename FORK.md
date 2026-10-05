# About this fork

Personal fork of [jleinenbach/GoogleFindMy-HA](https://github.com/jleinenbach/GoogleFindMy-HA).
Upstream changes are merged only after a manual security review of the diff.

Fork-specific changes:

- `chrome_driver.py`: on Windows the login helper no longer force-kills every running
  Chrome process (`taskkill /f /im chrome.exe`) before opening its own browser.
- Integration name changed to "Google Find Hub (fork)" (`manifest.json`, `hacs.json`); documentation and
  device "Visit" links point to this fork, the issue tracker to upstream.

- `diagnostics.py` / `redaction.py`: the diagnostics dump exported `shared_key`, `owner_key` and the
  e-mail-suffixed OAuth tokens from the imported secrets bundle in clear text (exact key match missed
  `owner_key_<email>` etc.). The whole `secrets_data` bundle, FCM registration and routing tokens are now
  redacted, and any key containing an e-mail address is redacted with the address masked.
- `api.py`: when the newest record is a coordinate-less SEMANTIC report (e.g. "at home"), coordinates of the
  freshest report from the previous hour are borrowed, so a tracker without a cached fix no longer stays `unknown`.

Releases of this fork are tagged `<upstream version>.<fork revision>` (e.g. `1.7.15.19.1`)
and carry a `googlefindmy.zip` asset built from `custom_components/googlefindmy/`, as HACS expects.
