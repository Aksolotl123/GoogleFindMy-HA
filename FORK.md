# About this fork

Personal fork of [jleinenbach/GoogleFindMy-HA](https://github.com/jleinenbach/GoogleFindMy-HA).
Upstream changes are merged only after a manual security review of the diff.

Fork-specific changes:

- `chrome_driver.py`: on Windows the login helper no longer force-kills every running
  Chrome process (`taskkill /f /im chrome.exe`) before opening its own browser.

Releases of this fork are tagged `<upstream version>.<fork revision>` (e.g. `1.7.15.19.1`)
and carry a `googlefindmy.zip` asset built from `custom_components/googlefindmy/`, as HACS expects.
