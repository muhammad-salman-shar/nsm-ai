package com.nsm.vb;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    private TextToSpeech tts;
    private ValueCallback<Uri[]> mUploadMessage;
    private volatile boolean isDestroyedFlag = false;
    private final static int FILECHOOSER_RESULTCODE = 1;
    private final static String LOCAL_URL = "http://127.0.0.1:8081";

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(Locale.US);
            }
        });

        webView = new WebView(this);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setCacheMode(WebSettings.LOAD_NO_CACHE);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (mUploadMessage != null) mUploadMessage.onReceiveValue(null);
                mUploadMessage = filePathCallback;
                Intent intent = fileChooserParams.createIntent();
                try {
                    startActivityForResult(intent, FILECHOOSER_RESULTCODE);
                } catch (Exception e) {
                    mUploadMessage = null;
                    return false;
                }
                return true;
            }
        });

        webView.addJavascriptInterface(new WebAppInterface(), "Android");
        setContentView(webView);

        String loadingHtml = "<html><body style='margin:0;background:#0b0f14;color:#eef3f9;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;text-align:center;'>"
                + "<div style='width:58px;height:58px;border-radius:18px;background:linear-gradient(135deg,#ff7e47,#ff4d1a);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:22px;margin-bottom:14px;box-shadow:0 10px 28px rgba(255,107,53,0.35);'>N</div>"
                + "<h2 style='margin:0 0 6px;'>NSM VB <span style='color:#ff6b35;'>v1.4</span></h2>"
                + "<p id='status' style='margin:0;color:#8c98a9;font-size:13px;'>Booting NeuraSaMu Cognitive Engine...</p>"
                + "<p id='err' style='color:#ef4444;font-size:12px;max-width:85%;margin-top:12px;'></p>"
                + "</body></html>";
        webView.loadData(loadingHtml, "text/html", "UTF-8");

        // Start Python Brain Server
        new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }
                String dataDir = getFilesDir().getAbsolutePath();
                PyObject pyServer = Python.getInstance().getModule("app_server");
                pyServer.callAttr("start_server", dataDir);
            } catch (Exception e) {
                final String safeErr = e.toString().replace("'", "").replace("\n", " ");
                runOnUiThread(() -> {
                    if (!isDestroyedFlag && webView != null) {
                        webView.evaluateJavascript("document.getElementById('err').innerText = '" + safeErr + "';", null);
                    }
                });
            }
        }).start();

        // Smart health-check polling instead of blind delay
        new Thread(() -> {
            for (int attempt = 0; attempt < 45 && !isDestroyedFlag; attempt++) {
                try {
                    URL url = new URL(LOCAL_URL + "/health");
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setConnectTimeout(600);
                    conn.setReadTimeout(600);
                    conn.setRequestMethod("GET");
                    int code = conn.getResponseCode();
                    conn.disconnect();
                    if (code == 200) {
                        runOnUiThread(() -> {
                            if (!isDestroyedFlag && webView != null) {
                                webView.loadUrl(LOCAL_URL);
                            }
                        });
                        return;
                    }
                } catch (Exception ignored) {
                }
                try {
                    Thread.sleep(300);
                } catch (InterruptedException ignored) {
                    return;
                }
            }
            runOnUiThread(() -> {
                if (!isDestroyedFlag && webView != null) {
                    webView.loadUrl(LOCAL_URL);
                }
            });
        }).start();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
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

    @Override
    protected void onDestroy() {
        isDestroyedFlag = true;
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }

    public class WebAppInterface {
        @JavascriptInterface
        public void speakText(String text) {
            if (tts != null && text != null) {
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
                File cacheDir = getCacheDir();
                File file = new File(cacheDir, fileName);
                FileWriter writer = new FileWriter(file);
                writer.write(brainJson);
                writer.close();

                Uri uri = androidx.core.content.FileProvider.getUriForFile(
                        MainActivity.this,
                        getPackageName() + ".fileprovider",
                        file
                );

                Intent shareIntent = new Intent(Intent.ACTION_SEND);
                shareIntent.setType("application/json");
                shareIntent.putExtra(Intent.EXTRA_STREAM, uri);
                shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                startActivity(Intent.createChooser(shareIntent, "Export NSM Brain"));
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Export failed: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }
    }
}
