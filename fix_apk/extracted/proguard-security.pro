# File Manager+ Security ProGuard Rules
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Aggressive obfuscation for security-sensitive classes
-repackageclasses 'a'
-allowaccessmodification
-overloadaggressively

# Remove logging
-assumenosideeffects class android.util.Log {
    public static int v(...);
    public static int d(...);
    public static int i(...);
}

# Obfuscate cloud integration classes
-keep,allowobfuscation class com.alphainventor.filemanager.file.** { *; }
