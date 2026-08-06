# iOS Share Sheet — one-time Xcode setup

The Android side of this feature (`android/`) works out of the box once you
open the project in Android Studio — Gradle picks up `.java` files under
`src/main/java/**` by convention, no manual project editing needed.

iOS has no equivalent convention: Xcode's project file (`.pbxproj`) has to
explicitly list every source file and every extension target, and that's a
generated, UUID-keyed file that's unsafe to hand-edit outside Xcode. So the
Swift code here (`ShareExtension/ShareViewController.swift` and
`App/App/ShareTargetPlugin.swift`) is correct and ready to use, but **won't
compile until you wire it up in Xcode** — a one-time step, same as adding
any custom native plugin to a Capacitor iOS app.

## 1. Add the main-app plugin file to the target

1. Open `ios/App/App.xcworkspace` (or `.xcodeproj` if no workspace yet) in Xcode.
2. Right-click the `App` group → **Add Files to "App"…**
3. Select `App/App/ShareTargetPlugin.swift`, make sure **Target: App** is checked.

That's the whole step for the main app — `CAPBridgedPlugin` conformance
means Capacitor auto-discovers it at runtime, no registration array to edit.

## 2. Create the Share Extension target

1. File → New → Target… → **Share Extension**. Name it `ShareExtension`.
2. When Xcode asks, let it generate its own `Info.plist` and
   `ShareViewController.swift` — then **delete those generated files** and
   add the ones from this repo instead:
   - Right-click the new `ShareExtension` group → Add Files… → select
     `ShareExtension/ShareViewController.swift` and
     `ShareExtension/Info.plist` from this repo, target: **ShareExtension** only.
3. In the extension's Info.plist (the one you just added), confirm it's set
   as the target's Info.plist under **Build Settings → Packaging → Info.plist File**.

## 3. Enable an App Group on both targets

The extension and the main app don't share memory — they hand off the file
through an [App Group](https://developer.apple.com/documentation/xcode/configuring-app-groups) container.

1. Select the **App** target → **Signing & Capabilities** → **+ Capability** → **App Groups**.
2. Add a group named `group.com.rinkodigital.app.share` (must match the
   `appGroupId` constant in both Swift files — change it in both places if
   you use a different reverse-DNS prefix than `com.rinkodigital.app`).
3. Repeat steps 1–2 for the **ShareExtension** target, same group ID.
4. This requires your own Apple Developer Team to be selected on both
   targets (Signing & Capabilities → Team) — App Groups are tied to your
   provisioning profile, which is why this can't be scripted from outside Xcode.

## 4. Build

Build the `App` scheme to a simulator or device. The share extension builds
as a dependency automatically. To test: open Photos (or the UniUni/GOFO
app), share an image, and "Rinko" should appear in the share sheet.

---

None of this was build-verified in the sandbox that generated it — there's
no Xcode here (Linux only). The Swift code compiles against documented
Capacitor/UIKit APIs and follows the standard "no-UI share extension +
App Group hand-off" pattern, but give it a real build once you've done the
steps above.
