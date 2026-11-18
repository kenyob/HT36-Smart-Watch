# HT36 project skills

Reverse-engineering skill packs discovered for this project, from **REAP** (REA Investigation Prompts,
`JoasASantos/REA-Prompts`, MIT — see `REAP-LICENSE`). These are paste-ready REA workflows. We keep only the
packs that fit this project; the full set of 26 is in the upstream repo.

| Skill | Use it for |
|---|---|
| `reap-00-install-and-verify` | Confirm REA + the JADX/Ghidra providers are connected before analysis |
| `reap-01-getting-started` | First-pass orientation on any target |
| `reap-02-feature-tracing-any-program` | **Trace a feature from the UI to the exact bytes it sends** — the core workflow for the BLE frames |
| `reap-08-android` | **Audit the WatchLink / GloryFitPro APK**: manifest, classes, methods, references |
| `reap-03-native-binary-exploration` | When we have a firmware dump / ADFU image to read |
| `reap-07-firmware-and-embedded` | Firmware regions + extraction (the ATS3085 image, later) |
| `reap-04-software-and-feature-cloning` | Re-implement a watch feature from the decompiled app into our page |
| `reap-15-version-comparison-and-crash-work` | Diff two app versions to spot a new/changed frame |
| `reap-16-long-running-investigations` | Keep an `INVESTIGATION.md` ledger across sessions |
| `reap-18-advanced-binary-exploration-and-deobfuscation` | If the app or firmware is obfuscated |
| `reap-21-protector-and-obfuscator-research` | Packed/protected-app triage |
| `reap-prompts` | The index of all REAP prompts |

## How REA gets the Android decompiler

REA's Android tools (`inspect_android_package`, etc.) need a caller-supplied **JADX MCP JAR** (`REA_JADX_MCP_JAR`)
and Java. Rick had neither, so we install `jadx` via Homebrew (it brings a JRE) and decompile directly; the JAR
can be wired into REA later. Decompiled app code is a **read-only reference** (AGENTS rule 3) — never installed or run.
