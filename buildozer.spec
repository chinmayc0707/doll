[app]
title = Tara Voice Assistant
package.name = tara
package.domain = org.test
source.dir = tara_app
source.include_exts = py,png,jpg,kv,atlas,wav,py
version = 0.1
requirements = python3,kivy,webrtcvad,pyaudio,requests,pybase64,numpy,noisereduce,speechrecognition,setuptools
orientation = portrait
fullscreen = 0

[android]
android.permissions = RECORD_AUDIO, INTERNET
android.api = 30
android.minapi = 21
android.sdk = 29
android.ndk = 21b
android.arch = armeabi-v7a
android.entrypoint = org.kivy.android.PythonActivity
android.activity.class_name = PythonActivity
android.private_storage = True
android.skip_update = False
android.wakelock = False
android.enable_androidx = True
p4a.branch = master
p4a.source_dir = .
p4a.bootstrap = sdl2
p4a.port = 8000
p4a.archs = armeabi-v7a
p4a.stl = c++_shared
p4a.hook =
p4a.presplash.filename = %(source.dir)s/icon.png
p4a.icon.filename = %(source.dir)s/icon.png
p4a.assets = .
p4a.min_api = 21
p4a.ndk_dir =
p4a.sdk_dir =
p4a.ignore_setup_py = False
p4a.local_recipes =
p4a.build_tools_version =
p4a.gradle_dependencies =
p4a.release_keystore =
p4a.release_keystore_alias =
p4a.release_keystore_password =
p4a.release_keystore_alias_password =

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = .buildozer
bin_dir = bin
p4a.source_dir = tara_app