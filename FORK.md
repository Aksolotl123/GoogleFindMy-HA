# About this fork

Personal fork of [jleinenbach/GoogleFindMy-HA](https://github.com/jleinenbach/GoogleFindMy-HA).
Upstream changes are merged only after a manual security review of the diff.

Fork-specific changes:

- `chrome_driver.py`: the login helper no longer kills existing Chrome processes before opening its own
  browser — neither on Windows (`taskkill /f /im chrome.exe`) nor on Linux/macOS (SIGTERM to every process
  with "chrome" in its command line). On teardown only the driver's own chromedriver process is killed,
  instead of every chromedriver on the machine (`taskkill /f /im chromedriver.exe`, `pgrep -f chromedriver`).
- Integration name changed to "Google Find Hub (fork)" (`manifest.json`, `hacs.json`); documentation and
  device "Visit" links point to this fork, the issue tracker to upstream.

- `diagnostics.py` / `redaction.py`: the diagnostics dump exported `shared_key`, `owner_key` and the
  e-mail-suffixed OAuth tokens from the imported secrets bundle in clear text (exact key match missed
  `owner_key_<email>` etc.). The whole `secrets_data` bundle, FCM registration and routing tokens are now
  redacted, and any key containing an e-mail address is redacted with the address masked (also when the
  value is empty, and for addresses containing "_"). `spot_token`, `adm_token`, `vapid_key` and `project_id`
  are redacted as well.
- `NovaApi/nova_request.py`: the account e-mail is masked in the AAS token TTL INFO/WARNING log lines.
- `api.py`: when the newest record is a coordinate-less SEMANTIC report (e.g. "at home"), coordinates of the
  freshest report from the previous hour are borrowed, so a tracker without a cached fix no longer stays `unknown`.
  The upstream test `test_async_get_device_location_marks_decrypt_proof_hidden_by_semantic` keeps its fix
  outside that hour (it guards the `_decrypt_proven` hint, not the missing coordinates); the borrowing itself is
  covered by `test_borrow_recent_coordinates_*` and `..._semantic_borrows_recent_fix`.

Releases of this fork are tagged `<upstream version>.<fork revision>` (e.g. `1.7.15.19.1`); since
`1.7.15.19.4` the version in `manifest.json` (with `const.py` and `pyproject.toml`) matches the tag.
Releases carry a `googlefindmy.zip` asset built from `custom_components/googlefindmy/`, as HACS expects.
