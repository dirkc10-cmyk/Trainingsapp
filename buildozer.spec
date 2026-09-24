[app]
title = TSV Holm Archery Coach PRO
package.name = tsvholmarcherycoach
package.domain = de.tsvholm
source.dir = .
source.include_exts = py,png,jpg,kv,json,atlas
version = 1.0.2
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Android build settings
android.api = 35
android.minapi = 23
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.permissions = READ_MEDIA_IMAGES
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
