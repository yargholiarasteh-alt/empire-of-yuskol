[app]
title = Empire of Yuskol
package.name = yuskol
package.domain = org.yuskol.empire
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,ttf,json
version = 3.0.0
requirements = python3,kivy,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
# Android APK build settings
android.api = 33
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
