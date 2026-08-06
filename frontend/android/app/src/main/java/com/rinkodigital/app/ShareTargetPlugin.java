package com.rinkodigital.app;

import android.content.ContentResolver;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.util.Base64;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

/**
 * Reads a file the OS handed us via the Share Sheet (android.intent.action.SEND)
 * and exposes it to the web layer as base64, so the JS side can turn it into a
 * Blob and upload it through the existing evidence-upload flow — no separate
 * native upload path to keep in sync with the backend.
 */
@CapacitorPlugin(name = "ShareTarget")
public class ShareTargetPlugin extends Plugin {

    @PluginMethod
    public void getSharedItem(PluginCall call) {
        Intent intent = getActivity().getIntent();
        JSObject result = readSharedIntent(intent);
        if (result == null) {
            call.resolve(new JSObject().put("present", false));
            return;
        }
        // Consume it so re-opening the app (or calling this again) doesn't
        // re-attach the same file a second time.
        getActivity().setIntent(new Intent());
        call.resolve(result);
    }

    /** Called by MainActivity#onNewIntent when a share arrives while the app is already open. */
    public void handleNewIntent(Intent intent) {
        JSObject result = readSharedIntent(intent);
        if (result != null) {
            notifyListeners("shareReceived", result);
        }
    }

    private JSObject readSharedIntent(Intent intent) {
        if (intent == null || !Intent.ACTION_SEND.equals(intent.getAction())) {
            return null;
        }
        Uri uri = intent.getParcelableExtra(Intent.EXTRA_STREAM);
        String mimeType = intent.getType();
        if (uri == null || mimeType == null) {
            return null;
        }

        ContentResolver resolver = getActivity().getContentResolver();
        try (InputStream input = resolver.openInputStream(uri)) {
            if (input == null) return null;

            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            byte[] chunk = new byte[8192];
            int read;
            while ((read = input.read(chunk)) != -1) {
                buffer.write(chunk, 0, read);
            }

            JSObject result = new JSObject();
            result.put("present", true);
            result.put("mimeType", mimeType);
            result.put("fileName", queryDisplayName(resolver, uri, mimeType));
            result.put("base64Data", Base64.encodeToString(buffer.toByteArray(), Base64.NO_WRAP));
            return result;
        } catch (IOException e) {
            return null;
        }
    }

    private String queryDisplayName(ContentResolver resolver, Uri uri, String mimeType) {
        try (Cursor cursor = resolver.query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (idx >= 0) {
                    String name = cursor.getString(idx);
                    if (name != null && !name.isEmpty()) return name;
                }
            }
        } catch (Exception ignored) {
            // Fall through to the generated name below.
        }
        String ext = mimeType.equals("image/png") ? "png"
            : mimeType.equals("image/webp") ? "webp"
            : mimeType.equals("application/pdf") ? "pdf"
            : "jpg";
        return "shared-" + System.currentTimeMillis() + "." + ext;
    }
}
