[app]
title = StockMonitor
package.name = stockmonitor
package.domain = com.yourname
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttc,ttf
version = 0.1
requirements = python3,kivy,requests,charset-normalizer,idna,urllib3,certifi,beautifulsoup4,soupsieve
orientation = portrait
fullscreen = 0

# Android 專屬權限 (必須開通網路權限才能爬蟲)
android.permissions = INTERNET

# Android API 版本設定
android.api = 33
android.minapi = 21
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1