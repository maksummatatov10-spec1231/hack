# ============================================
# File Manager+ Security Rules
# ============================================

# Keep security-critical classes
-keep class com.alphainventor.filemanager.service.CommandService { *; }
-keep class com.alphainventor.filemanager.service.FtpServerService { *; }
-keep class com.alphainventor.filemanager.service.HttpServerService { *; }

# Obfuscate cloud helper classes more aggressively
-repackageclasses com.alphainventor.filemanager.file
-allowaccessmodification
-overloadaggressively

# Remove logging in release
-assumenosideeffects class android.util.Log {
    public static int v(...);
    public static int d(...);
    public static int i(...);
}

# Keep WebView JavaScript interface (if any)
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Obfuscate string constants
-obfuscationdictionary /home/user/dict.txt
-classobfuscationdictionary /home/user/dict.txt
-packageobfuscationdictionary /home/user/dict.txt
