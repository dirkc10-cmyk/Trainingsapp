TSV Holm Archery Coach PRO – FINAL116 MOBILE

ANDROID-BUILD

Variante A – GitHub Actions (einfachste Variante)
1. Alle Dateien dieses Ordners in ein eigenes GitHub-Repository laden.
2. Im Repository: Actions -> Build FINAL116 Android APK -> Run workflow.
3. Nach dem Lauf unter Artifacts das APK-Paket herunterladen.
4. APK auf das Android-Handy übertragen und installieren.

Variante B – Linux/WSL2
1. In diesem Ordner ein Terminal öffnen.
2. ./build_android.sh ausführen.
3. Das Ergebnis liegt normalerweise in bin/*.apk.

DATENÜBERNAHME
- In FINAL115: Datenverwaltung -> JSON exportieren.
- JSON aufs Android-Gerät kopieren.
- FINAL116 MOBILE: Datenverwaltung -> JSON importieren.

HINWEIS
Die APK wird hier nicht vorab mitgeliefert, weil in dieser Ausführungsumgebung keine Android SDK/NDK/Buildozer-Toolchain vorhanden ist. Der enthaltene GitHub-Workflow baut die Debug-APK reproduzierbar in einer Linux-Buildumgebung.
