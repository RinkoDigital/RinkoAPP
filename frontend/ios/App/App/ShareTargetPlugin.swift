import Foundation
import Capacitor

/// Reads whatever ShareExtension/ShareViewController.swift dropped into the
/// shared App Group container and hands it to the JS layer as base64 — the
/// exact same shape (present/mimeType/fileName/base64Data) the Android
/// ShareTargetPlugin returns, so frontend/src/native/shareTarget.ts needs
/// no per-platform branching.
///
/// This file must be added to the "App" target's Compile Sources in Xcode
/// (it's on disk, but Xcode won't pick it up automatically) — see
/// ../../SHARE_EXTENSION_SETUP.md.
@objc(ShareTargetPlugin)
public class ShareTargetPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "ShareTargetPlugin"
    public let jsName = "ShareTarget"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "getSharedItem", returnType: CAPPluginReturnPromise)
    ]

    private let appGroupId = "group.com.rinkodigital.app.share"

    @objc func getSharedItem(_ call: CAPPluginCall) {
        guard
            let defaults = UserDefaults(suiteName: appGroupId),
            let fileName = defaults.string(forKey: "pendingShareFileName"),
            let mimeType = defaults.string(forKey: "pendingShareMimeType"),
            let container = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupId)
        else {
            call.resolve(["present": false])
            return
        }

        let fileURL = container.appendingPathComponent("pending-share").appendingPathComponent(fileName)
        guard let data = try? Data(contentsOf: fileURL) else {
            call.resolve(["present": false])
            return
        }

        // Consume it so the same file isn't attached twice.
        defaults.removeObject(forKey: "pendingShareFileName")
        defaults.removeObject(forKey: "pendingShareMimeType")
        try? FileManager.default.removeItem(at: fileURL)

        call.resolve([
            "present": true,
            "mimeType": mimeType,
            "fileName": fileName,
            "base64Data": data.base64EncodedString(),
        ])
    }
}
