[app]
title = TSV Holm Archery Coach PRO
package.name = tsvholmarcherycoach
package.domain = de.tsvholm
source.dir = .
source.include_exts = py,png,jpg,kv,json,atlas
version = 1.0.3
requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.permissions = READ_MEDIA_IMAGES
android.accept_sdk_license = True

p4a.python_version = 3.11

[buildozer]
log_level = 2
warn_on_root = 1
