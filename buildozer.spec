[app]
title = TSV Holm Archery Coach PRO
package.name = tsvholmarcherycoach
package.domain = de.tsvholm
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json
source.exclude_exts = spec
source.exclude_dirs = bin,.buildozer,__pycache__
version = 1.0.4
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

p4a.python_version = 3.11

[buildozer]
log_level = 2
warn_on_root = 1
