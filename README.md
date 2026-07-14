# tube_vintage

## Phase 3.0.2

Le flux OTA est maintenant en deux temps :

- Téléchargement vers des fichiers `.new` en environnement minimal ;
- Installation minimale ensuite, après redémarrage, pour convertir `.new` en fichiers finaux avec sauvegarde `.bak`.

La version de l'application ne bascule pas encore automatiquement avec confirmation de démarrage ni rollback automatique après redémarrage.

## Manifeste Netlify

Le manifeste référence des fichiers locaux destinés aux tests OTA :

- `install_test_small.txt` provient de `update_test_small.txt`
- `install_test_large.txt` provient de `update_test_large.txt`

Exemple de structure :

```json
{
  "manifest_version": 1,
  "version": "3.0.6",
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

Les fichiers distants sont téléchargés sous `name + ".new"` :

- `install_test_small.txt.new`
- `install_test_large.txt.new`

## Démarrage OTA au boot

`boot.py` applique désormais la priorité :

1. Si `ota_install_pending.json` existe : lancer `ota_installer.py` ;
2. Sinon si `ota_download_pending.json` existe : lancer `ota_downloader.py` ;
3. Sinon : laisser le démarrage normal de MicroPython (`main.py`).

Pendant un cycle installateur, `main.py` n’est pas lancé manuellement.

## Marqueurs

### `ota_download_pending.json` (téléchargement)

Créé par `updater.py` après détection d’une version plus récente.

### `ota_install_pending.json` (installation)

Créé par `ota_downloader.py` uniquement après :

- téléchargement réussi,
- validation de la taille,
- validation SHA-256,
- présence des `.new`.

Format minimal requis :

```json
{
  "version": 1,
  "remote_version": "3.0.6",
  "files": [
    {
      "name": "install_test_small.txt"
    },
    {
      "name": "install_test_large.txt"
    }
  ]
}
```

### `ota_install_ready.json` (optionnel)

Créé après installation réussie.

## Module `ota_installer.py`

`ota_installer.py` est minimal et ne dépend que de :

- `os`
- `time`
- `machine`
- `ota_state` (lecture/écriture marqueurs, validation noms)

### Comportement d’installation

Pour chaque nom de fichier du marqueur :

1. vérification préalable de `<name>.new` ;
2. suppression d’un `.bak` existant uniquement dans le flux contrôlé de test ;
3. sauvegarde de `<name>` en `<name>.bak` si présent ;
4. remplacement de `<name>.new` vers `<name>` ;
5. journalisation des étapes pour restauration.

En cas d’échec :

- arrêt immédiat ;
- restauration de toutes les opérations déjà réalisées (ordre inverse) ;
- nettoyage des `.new` ;
- suppression des marqueurs d’installation ;
- redémarrage vers `main.py`.

### Simulation d’échec

Un drapeau de diagnostic est présent dans `ota_installer.py` :

`INSTALL_TEST_FAIL_ON_INDEX = 1`

- `None` par défaut (mode normal)
- `1` provoque une erreur au second fichier pour valider la restauration.

## Fichiers interdits aux fichiers installables

La validation bloque :

- `wifi_secrets.py`
- `time_state.json`
- `runtime_state.json`
- `ota_download_pending.json`
- `ota_download_ready.json`
- `ota_install_pending.json`
- `ota_install_ready.json`
- tous les `.new`
- tous les `.bak`
- marqueurs internes OTA
- profils/ressources actives (ex. `main.py`, `config.py`, `boot.py`) et fichiers de développement.

## Tests de base à documenter

### Test 1 : installation réussie

1. Créer manuellement sur l’ESP32 :
   - `install_test_small.txt` avec `ANCIEN CONTENU PETIT`
   - `install_test_large.txt` avec `ANCIEN CONTENU GROS`
2. Lancer la mise à jour OTA (téléchargement + redémarrage).
3. Vérifier après retour :
   - `install_test_small.txt` contient le nouveau contenu,
   - `install_test_small.txt.bak` contient `ANCIEN CONTENU PETIT`,
   - `install_test_large.txt` contient le nouveau contenu,
   - `install_test_large.txt.bak` contient `ANCIEN CONTENU GROS`,
   - aucun `.new` résiduel.

### Test 2 : échec simulé sur le second fichier

1. Réinitialiser les anciens contenus.
2. Activer `INSTALL_TEST_FAIL_ON_INDEX = 1` dans `ota_installer.py`.
3. Relancer le cycle.
4. Vérifier :
   - le premier fichier revenu à son ancien contenu,
   - le second fichier non mélangé (ancien contenu maintenu),
   - aucun `.new`/final incorrect,
   - retour correct vers `main.py`.

## Comportements conservés en phase 3.0.2

- `main.py`, `config.py`, modules actifs, Wi-Fi/NTP/LED/profil logique, modules solaires et logique horaire ne sont pas modifiés pour l’OTA.
- pas de confirmation de démarrage,
- pas de compteur de redémarrages de version,
- pas d’effacement automatique des `.bak`,
- pas de remplacement réel de `main.py` / `config.py`.
