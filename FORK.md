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
- `services.py`: the maintenance services `refresh_device_urls`, `rebuild_device_registry` and `rebuild_registry`
  (registry rewrites, entity/device removal, config-entry reloads) are restricted to administrators, with the same
  check as Core's `async_register_admin_service` (a non-admin user gets `Unauthorized`; automations and scripts
  still run them). Locate and sound services stay available to every user.
- Account e-mail out of the logs: `entry.title` (the account address) is no longer logged at INFO
  (`services.py` hub cleanup, `__init__.py` ignored-device message — the entry id is logged instead);
  `get_owner_key.py` masks the address as `j***@example.com` and logs only the error type of a decoding failure.
- `redaction.py`: key names match regardless of case and naming style (`Access-Token`, `accessToken`, `EMAIL`),
  tuples are redacted like lists.
- `diagnostics.py`: free-form text in the diagnostics buffer (`error_msg`, `arg`, `reason`, …) is exported as type
  and length only; `secrets_extra_watch_paths` (home directory / OS user name) is exported as a count of placeholders.

Releases of this fork are tagged `<upstream version>.<fork revision>` (e.g. `1.7.15.19.1`); since
`1.7.15.19.4` the version in `manifest.json` (with `const.py` and `pyproject.toml`) matches the tag.
Releases carry a `googlefindmy.zip` asset built from `custom_components/googlefindmy/`, as HACS expects.
