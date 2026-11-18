# GloryFitPro APK — how to get it

The public APK mirrors (APKPure, APKMirror) sit behind Cloudflare bot challenges, so a plain download
returns a challenge page, not the APK. Defeating that is off-limits. Use the clean route:

## From the owner's Android phone (Play Store → adb pull)
```bash
# 1. Install "GloryFitPro" from the Play Store on the phone.
# 2. Enable USB debugging, plug the phone into the Mac.
adb shell pm path com.yc.gloryfitpro          # prints: package:/data/app/.../base.apk
adb pull /data/app/.../base.apk gloryfitpro.apk
```

Then it can be decompiled with REA for static analysis only (never installed here, per AGENTS rule 3).
Package: `com.yc.gloryfitpro` · SDK `com.yc.nadalsdk` (vendor UTE / Youchuangyi).
