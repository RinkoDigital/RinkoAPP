package com.rinkodigital.app;

import android.content.Intent;
import android.os.Bundle;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.PluginHandle;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ShareTargetPlugin.class);
        super.onCreate(savedInstanceState);
    }

    @Override
    public void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);

        PluginHandle handle = getBridge().getPlugin("ShareTarget");
        if (handle != null && handle.getInstance() instanceof ShareTargetPlugin) {
            ((ShareTargetPlugin) handle.getInstance()).handleNewIntent(intent);
        }
    }
}
