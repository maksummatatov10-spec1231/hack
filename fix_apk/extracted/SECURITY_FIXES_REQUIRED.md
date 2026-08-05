# Security Fixes Required (Code Changes)

## Critical Fixes

### 1. BookmarkProvider.java - SQL Injection Fix
```java
// BEFORE (vulnerable):
String where = "_id=" + id + " and (" + selection + ")";
db.delete("bookmarks", where, selectionArgs);

// AFTER (safe):
String where = "_id=? AND (" + selection + ")";
String[] args = new String[]{id};
if (selectionArgs != null) {
    args = ArrayUtils.addAll(new String[]{id}, selectionArgs);
}
db.delete("bookmarks", where, args);
```

### 2. WebViewActivity.java - XSS Fix
```java
// BEFORE (vulnerable):
mWebView.getSettings().setJavaScriptEnabled(true);

// AFTER (safe):
// Add URL whitelist
private static final List<String> ALLOWED_DOMAINS = Arrays.asList(
    "dropbox.com", "box.com", "pcloud.com", "yandex.com", "yandex.ru"
);

public boolean shouldOverrideUrlLoading(WebView view, String url) {
    Uri uri = Uri.parse(url);
    String host = uri.getHost();
    if (host != null && ALLOWED_DOMAINS.stream().anyMatch(host::endsWith)) {
        view.loadUrl(url);
    } else {
        Log.w("Security", "Blocked URL: " + url);
    }
    return true;
}
```

### 3. FtpServerService.java - Password Encryption
```java
// BEFORE (vulnerable):
String password = intent.getStringExtra("extra_password");

// AFTER (safe):
// Use EncryptedSharedPreferences
MasterKey masterKey = new MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build();
SharedPreferences prefs = EncryptedSharedPreferences.create(
    context, "ftp_secure_prefs", masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
);
String password = prefs.getString("ftp_password", null);
```

### 4. FileObserverService.java - Path Traversal Fix
```java
// BEFORE (vulnerable):
String filepath = intent.getStringExtra("filepath");
if (new File(filepath).exists()) { ... }

// AFTER (safe):
String filepath = intent.getStringExtra("filepath");
File file = new File(filepath);
String canonicalPath = file.getCanonicalPath();
String allowedBase = Environment.getExternalStorageDirectory().getCanonicalPath();
if (!canonicalPath.startsWith(allowedBase)) {
    throw new SecurityException("Path traversal detected: " + filepath);
}
if (file.exists()) { ... }
```

### 5. HttpServerService.java - Add Authentication
```java
// Add token-based authentication
String authToken = UUID.randomUUID().toString();
// Store in EncryptedSharedPreferences
// Pass token in URL: http://ip:port?token=xxx
// Validate token in request handler
```
