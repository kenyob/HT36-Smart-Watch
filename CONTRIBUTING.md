# Contributing

Thanks for helping open up the HT36. Most of the work is protocol detective work plus small, testable additions
to one web page, so you don't need the exact watch to help: protocol reading, the GPX/health importers and the
UI are all open.

## Where things happen
- **Issues and pull requests: on this GitHub repo.** Start with issues labelled
  [`good first issue`](../../labels/good%20first%20issue) or [`help wanted`](../../labels/help%20wanted).
- Labels: `area/protocol`, `area/web-app`, `area/health-data`, `area/gps`, `area/faces`, `area/audio`, and
  `needs-wrist-test` (needs someone with the watch).

## Run it
```bash
cd Control-Page
python3 server.py                 # http://localhost:8736/ in Chrome or Edge
python3 -m unittest test_server   # must pass before a PR
```
Python 3.9+ standard library only for the service. The page is one file (`Control-Page/page-body.html`: HTML,
CSS and JS); keep it dependency-free apart from the Leaflet map that loads at runtime.

## Ground rules (they protect people's watches)
1. **Never write to the firmware-update (OTA) service** (`e49a3001…` / `e49a3002…`). The page doesn't even list it
   in `optionalServices`, and a test checks that. PRs that touch OTA will not be merged.
2. **Queries before sets.** New frames go in as read-only queries (`01 <grp> AA …`) first. A set (`AB`) needs a
   source: a vendor-app builder reference in `docs/06`, a capture, or a tested result.
3. **Mark new controls "mapped · untested"** until someone confirms them on the wrist. Use the page's Works / Doesn't
   buttons and say what you saw in the PR or issue.
4. **No vendor code, APKs, firmware or assets in the repo.** Describe protocol facts in your own words (frame
   layouts, field meanings), and cite the vendor class or method only as a reference.
5. **No personal data in commits:** no watch MAC, no exported health data, no voice notes, no logs with your
   location. The `data/` and `logs/` folders are git-ignored for that reason.

## Sharing a capture or a new frame
- From the page: **Bluetooth log → Download JSON** after reproducing what you saw. Remove anything personal and
  attach it to the issue using the "Frame report" template.
- From an Android phone: Developer options → *Bluetooth HCI snoop log*, use the vendor app, then attach the
  relevant frames as hex. Don't attach the full bugreport: it holds personal data.

## Where to read first
`docs/05-app-controls.md` (WatchLink frames), `docs/06-gloryfitpro-protocol-and-versions.md` (full SDK map),
`docs/04-plan-all-features.md` (roadmap), `docs/07-testing-plan-and-log.md` (how we test).

## Code of conduct
Be kind, assume good faith, and keep discussion about the work.
