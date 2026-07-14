# tube_vintage

## Phase 3.0.3 — confirmation de démarrage OTA

Le flux OTA reste en trois états :

1. `ota_download_pending.json` / `ota_download_ready.json` (téléchargement validé)
2. `ota_install_pending.json` (installation en cours)
3. `ota_boot_pending.json` (nouvelle version en cours de confirmation)

`main.py` n’est pas encore mis à jour par OTA dans cette phase, mais la version active peut être confirmée après un démarrage stable.

## Manifeste Netlify (version de test)

`netlify/version.json` référence maintenant :

- `install_test_small.txt` (depuis `update_test_small.txt`)
- `install_test_large.txt` (depuis `update_test_large.txt`)

```json
{
  "manifest_version": 1,
  "version": "3.0.7",
  "files": [
    {
      "name": "install_test_small.txt",
      "url": "https://tube-vintage-jfb.netlify.app/firmware/update_test_small.txt",
      "size": 47,
      "sha256": "cadc0f4bd5f798181999e5fffb1b73f4120ee95e48886e6bdefee6e2a9665ca9"
    },
    {
      "name": "install_test_large.txt",
      "url": "https://tube-vintage-jfb.netlify.app/firmware/update_test_large.txt",
      "size": 65536,
      "sha256": "9d7ea698f1fec4d98ec3fc69a897b009113be8a032b7c6585de47421382de6f1"
    }
  ]
}
```

## Ordre de démarrage `boot.py`

1. `ota_boot_pending.json` (priorité haute) :
   - incrémente `boot_attempts`
   - laisse démarrer `main.py` tant que la limite n’est pas dépassée
   - si dépassée, lance `ota_rollback.py`
2. `ota_install_pending.json` → `ota_installer.py`
3. `ota_download_pending.json` → `ota_downloader.py`
4. sinon, démarrage normal `main.py`

## Nouveau marqueur de confirmation `ota_boot_pending.json`

Créé par `ota_installer.py` après une installation réussie :

```json
{
  "version": 1,
  "remote_version": "3.0.7",
  "files": [
    {
      "name": "install_test_small.txt",
      "backup": "install_test_small.txt.bak",
      "had_previous_file": true
    }
  ],
  "boot_attempts": 0,
  "max_boot_attempts": 3
}
```

Un fichier sans version précédente est représenté avec `"had_previous_file": false`.

## Fichiers créés

- `ota_rollback.py`
- `ota_boot_pending.json` (marqueur dynamique)
- `ota_update_confirmed.json` (facultatif, créé quand la confirmation réussit)

## Comportement installateur

`ota_installer.py` :

- vérifie tous les `.new`,
- crée les `.bak` des fichiers existants,
- installe les `.new`,
- en cas d’échec, restaure immédiatement les fichiers déjà installés,
- crée `ota_boot_pending.json` uniquement si :
  - tous les fichiers sont installés,
  - tous les `.bak` requis existent,
  - aucune erreur d’installation n’est survenue.

`ota_state.py` contient :
- création / chargement / suppression de `ota_boot_pending.json`,
- validation stricte du marqueur,
- `confirm_boot_success()` :
  - supprime les `.bak`,
  - supprime le marqueur,
  - peut créer `ota_update_confirmed.json`.

## Restaurateur `ota_rollback.py`

- vérifie la présence de `ota_boot_pending.json`,
- restaure les fichiers selon `had_previous_file` :
  - si `true` : remplace le nouveau fichier par son `.bak`,
  - si `false` : supprime le fichier installé,
- nettoie les `.new`,
- retire les marqueurs de confirmation partiels,
- crée `ota_rollback_done.json` en cas de restauration incomplète,
- redémarre vers la version précédente.

## Limite de tentative

- `MAX_ATTEMPTS = 3` (défaut)
- tentatives 1..3 : la version peut démarrer
- à la tentative 4 : rollback automatique

## Simulation de rollback volontaire

- paramètre présent dans `main.py` : `SIMULATE_NO_BOOT_CONFIRM`
- valeur par défaut : `False`
- passer à `True` pour empêcher la confirmation et déclencher le rollback après dépassement du seuil.

## Messages de référence

- démarrage de confirmation : `OTA : demarrage de la nouvelle version a confirmer`
- tentative de démarrage : `OTA : tentative de demarrage X / 3`
- confirmation OK : `OTA : nouvelle version stable`
- confirmation faite : `OTA : demarrage confirme`
- suppression backups : `OTA : suppression des sauvegardes .bak terminee`
- rollback : 
  - `OTA rollback : demarrage`
  - `OTA rollback : restauration de ...`
  - `OTA rollback : restauration terminee`
  - `OTA rollback : redemarrage vers l'ancienne version`

## Fichiers critiques bloqués aux OTA

`wifi_secrets.py`, `time_state.json`, `runtime_state.json`,
`ota_download_pending.json`, `ota_download_ready.json`,
`ota_install_pending.json`, `ota_install_ready.json`,
`ota_boot_pending.json`, `ota_update_confirmed.json`,
`ota_rollback_done.json`, tous les `.new`, tous les `.bak`, marqueurs OTA internes.

## Ce qui reste inchangé

- confirmation uniquement via marqueur `ota_boot_pending.json` (pas de mécanisme externe),
- pas d’installation OTA réelle de `main.py` / `config.py` dans cette phase,
- pas de récupération OTA automatique avant version suivante.
