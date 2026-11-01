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
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.widget.Toast;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    private TextToSpeech tts;
    private ValueCallback<Uri[]> mUploadMessage;
    private final static int FILECHOOSER_RESULTCODE = 1;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Initialize Native TTS
        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                if (status == TextToSpeech.SUCCESS) {
                    tts.setLanguage(Locale.US);
                }
            }
        });

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

        webView.addJavascriptInterface(new WebAppInterface(), "Android");

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
                // Get the app's writable internal storage directory
                String dataDir = getFilesDir().getAbsolutePath();
                PyObject pyServer = Python.getInstance().getModule("app_server");
                pyServer.callAttr("start_server", dataDir);
            } catch (Exception e) {
                final String err = e.toString();
                runOnUiThread(() -> webView.evaluateJavascript("document.getElementById('err').innerText = '" + err + "';", null));
            }
        }).start();

        // Retry loading the page after 3 seconds
        webView.postDelayed(() -> webView.loadUrl("http://127.0.0.1:8081"), 5000);
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

    public class WebAppInterface {
        @JavascriptInterface
        public void speakText(String text) {
            if (tts != null) {
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "NSM_TTS");
            }
        }

        @JavascriptInterface
        public void stopTTS() {
            if (tts != null) {
                tts.stop();
            }
        }

        @JavascriptInterface
        public void shareBrain(String brainJson, String fileName) {
            try {
                // Save to cache directory first
                java.io.File cacheDir = getCacheDir();
                java.io.File file = new java.io.File(cacheDir, fileName);
                java.io.FileWriter writer = new java.io.FileWriter(file);
                writer.write(brainJson);
                writer.close();

                // Create share intent
                android.net.Uri uri = androidx.core.content.FileProvider.getUriForFile(
                    MainActivity.this,
                    getPackageName() + ".fileprovider",
                    file
                );

                Intent shareIntent = new Intent(Intent.ACTION_SEND);
                shareIntent.setType("application/json");
                shareIntent.putExtra(Intent.EXTRA_STREAM, uri);
                shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                startActivity(Intent.createChooser(shareIntent, "Export Brain File"));
            } catch (Exception e) {
                Toast.makeText(MainActivity.this, "Export failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
            }
        }
    }

}
