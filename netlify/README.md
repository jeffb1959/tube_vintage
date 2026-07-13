# Publication Netlify

Ce dossier prepare les fichiers statiques qui seront publies sur Netlify.
`version.json` est seulement consulte pendant la phase 3.0.0 : aucun fichier de
`firmware/` n'est encore telecharge ou installe par l'ESP32.

Avant le deploiement, remplacer `votre-site.netlify.app` dans le manifeste et
dans `updater.py` par le domaine Netlify reel.

Ne jamais placer ici `wifi_secrets.py`, `time_state.json` ou un autre fichier
local ou secret.
