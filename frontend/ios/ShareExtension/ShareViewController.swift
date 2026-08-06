import UIKit
import UniformTypeIdentifiers

/// No-UI-needed share extension: grabs the shared image/PDF, drops it into
/// the App Group container the main Rinko app also has access to, then
/// closes itself. `ShareTargetPlugin.swift` (in the main app target) picks
/// it up the next time the app is foregrounded — same JS-facing contract
/// (present/mimeType/fileName/base64Data) the Android ShareTargetPlugin
/// exposes, so frontend/src/native/shareTarget.ts works unchanged on both
/// platforms.
///
/// This file only compiles once it's part of a "Share Extension" Xcode
/// target — see ../SHARE_EXTENSION_SETUP.md for the manual Xcode steps
/// (creating that target isn't something that can be done from a plain
/// file write; it edits Xcode's own project format).
class ShareViewController: UIViewController {
    private let appGroupId = "group.com.rinkodigital.app.share"

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black

        let label = UILabel()
        label.text = "Salvando no Rinko…"
        label.textColor = .white
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])

        handleSharedItem()
    }

    private func handleSharedItem() {
        guard
            let item = extensionContext?.inputItems.first as? NSExtensionItem,
            let attachment = item.attachments?.first
        else {
            close()
            return
        }

        let imageType = UTType.image.identifier
        let pdfType = UTType.pdf.identifier

        if attachment.hasItemConformingToTypeIdentifier(imageType) {
            attachment.loadItem(forTypeIdentifier: imageType, options: nil) { [weak self] data, _ in
                self?.saveAndClose(data: data, fallbackExt: "jpg", mimeType: "image/jpeg")
            }
        } else if attachment.hasItemConformingToTypeIdentifier(pdfType) {
            attachment.loadItem(forTypeIdentifier: pdfType, options: nil) { [weak self] data, _ in
                self?.saveAndClose(data: data, fallbackExt: "pdf", mimeType: "application/pdf")
            }
        } else {
            close()
        }
    }

    private func saveAndClose(data: NSSecureCoding?, fallbackExt: String, mimeType: String) {
        var fileData: Data?
        var fileName = "shared-\(Int(Date().timeIntervalSince1970)).\(fallbackExt)"

        if let url = data as? URL {
            fileData = try? Data(contentsOf: url)
            fileName = url.lastPathComponent
        } else if let image = data as? UIImage {
            fileData = image.jpegData(compressionQuality: 0.92)
        } else if let raw = data as? Data {
            fileData = raw
        }

        guard
            let bytes = fileData,
            let container = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupId)
        else {
            close()
            return
        }

        let pendingDir = container.appendingPathComponent("pending-share", isDirectory: true)
        try? FileManager.default.createDirectory(at: pendingDir, withIntermediateDirectories: true)
        let fileURL = pendingDir.appendingPathComponent(fileName)
        try? bytes.write(to: fileURL)

        let defaults = UserDefaults(suiteName: appGroupId)
        defaults?.set(fileName, forKey: "pendingShareFileName")
        defaults?.set(mimeType, forKey: "pendingShareMimeType")

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { [weak self] in
            self?.close()
        }
    }

    private func close() {
        extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
    }
}
