package com.nsm.vb;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    private ValueCallback<Uri[]> mUploadMessage;
    private final static int FILECHOOSER_RESULTCODE = 1;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (mUploadMessage != null) mUploadMessage.onReceiveValue(null);
                mUploadMessage = filePathCallback;
                Intent intent = fileChooserParams.createIntent();
                try { startActivityForResult(intent, FILECHOOSER_RESULTCODE); } 
                catch (Exception e) { mUploadMessage = null; return false; }
                return true;
            }
        });

        setContentView(webView);

        // Show Loading Screen
        String loadingHtml = "<html><body style='background:#0d1117;color:white;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;text-align:center;'>" +
                "<div><h2>NSM VB</h2><p>Starting Brain Engine...</p><p id='err' style='color:red;font-size:12px;'></p></div>" +
                "</body></html>";
        webView.loadData(loadingHtml, "text/html", "UTF-8");

        // Start Python Server
        new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }
                PyObject pyServer = Python.getInstance().getModule("app_server");
                pyServer.callAttr("start_server");
            } catch (Exception e) {
                final String err = e.toString();
                runOnUiThread(() -> webView.evaluateJavascript("document.getElementById('err').innerText = '" + err + "';", null));
            }
        }).start();

        // Retry loading the page after 3 seconds
        webView.postDelayed(() -> webView.loadUrl("http://127.0.0.1:8081"), 3000);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILECHOOSER_RESULTCODE) {
            if (mUploadMessage == null) return;
            Uri[] results = null;
            if (resultCode == Activity.RESULT_OK && data != null) {
                String dataString = data.getDataString();
                if (dataString != null) results = new Uri[]{Uri.parse(dataString)};
            }
            mUploadMessage.onReceiveValue(results);
            mUploadMessage = null;
        }
    }
}
