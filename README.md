# tube_vintage

## Phase 3.0.0

Cette phase ajoute une premiere verification de version depuis un manifeste
statique publie sur Netlify. L'ESP32 consulte et valide `version.json`, compare
sa version locale a la version distante et indique si une mise a jour existe.

Aucun fichier de programme n'est telecharge, ecrit, renomme ou installe dans
cette phase. Aucun redemarrage n'est effectue.

## Configuration Netlify

L'URL technique se trouve dans `updater.py` :

```python
VERSION_MANIFEST_URL = "https://votre-site.netlify.app/version.json"
```

Remplacer explicitement `votre-site.netlify.app` par le domaine Netlify reel
avant le deploiement. Cette URL ne doit pas etre placee dans `config.py`.

Le dossier local `netlify/` prepare la future publication :

```text
netlify/
|-- version.json
|-- README.md
`-- firmware/
    `-- README.md
```

## Manifeste

L'exemple `netlify/version.json` contient :

```json
{
  "manifest_version": 1,
  "version": "3.0.0",
  "files": [
    {
      "name": "main.py",
      "url": "https://votre-site.netlify.app/firmware/main.py",
      "size": 0,
      "sha256": ""
    },
    {
      "name": "config.py",
      "url": "https://votre-site.netlify.app/firmware/config.py",
      "size": 0,
      "sha256": ""
    }
  ]
}
```

Pour cette phase, `manifest_version` doit valoir `1`, `version` doit etre une
version numerique valide et `files`, si present, doit etre une liste de
dictionnaires. `size` et `sha256` ne sont pas encore verifies.

## Verification et comparaison

Apres une nouvelle connexion Wi-Fi, `updater.py` attend 15 secondes avec une
echeance monotone avant de consulter Netlify. Ce delai espace la requete des
operations NTP et Open-Meteo.

- apres une verification reussie, la suivante est planifiee dans 24 heures;
- apres un echec reseau, HTTP ou JSON, un nouvel essai est planifie dans une
  heure;
- la reponse HTTP est fermee dans tous les cas;
- tout l'etat reste uniquement en RAM.

Les versions sont converties en trois entiers `(majeur, mineur, correctif)` et
ne sont jamais comparees comme de simples chaines. Ainsi `3.0.10` est bien
superieur a `3.0.9`. Une version incomplete, non numerique ou comportant un
nombre different de composantes invalide le manifeste.

Une version distante superieure est seulement annoncee et memorisee en RAM.
Les LED, le bouton, les profils et tous les gestionnaires continuent leur
fonctionnement normal.

## Diagnostic depuis Thonny

Pour rendre la prochaine verification immediate lorsque le Wi-Fi est connecte :

```python
import updater
updater.force_check()
```

Pour consulter l'etat en RAM :

```python
updater.get_state()
```

Cette commande ne change pas la version locale et ne telecharge aucun fichier.

## Futur perimetre des mises a jour

Le manifeste pourra inclure les modules fonctionnels du projet, notamment :

- `main.py`;
- `config.py`;
- `wifi_manager.py`;
- `time_manager.py`;
- `time_safety.py`;
- `schedule_manager.py`;
- `sun_manager.py`;
- `night_profile_manager.py`;
- `updater.py`;
- tout autre module fonctionnel publie avec le micrologiciel.

`config.py` fera volontairement partie des futures mises a jour. Les reglages
locaux qu'il contient pourront donc etre remplaces par une version distante.

Les elements suivants ne devront jamais etre remplaces par Netlify :

- `wifi_secrets.py`;
- `time_state.json`;
- les fichiers temporaires `.new`;
- les sauvegardes `.bak`;
- les marqueurs internes de mise a jour;
- les fichiers locaux de developpement;
- `.gitignore`;
- `package.json` et `package-lock.json`;
- `pyrightconfig.json`;
- le dossier `.vscode`;
- le dossier `node_modules`.

## Fonctionnement existant conserve

- ESP32 DevKit V1, cinq LED WS2812 sur GPIO 5 et bouton sur GPIO 27;
- quatre profils visuels et passage automatique temporaire a `NUIT`;
- Wi-Fi non bloquant et synchronisation NTP toutes les 6 heures;
- heure locale du Quebec et horaire automatique de 06:00 a 00:00;
- securite temporelle et grace de 72 heures;
- recuperation quotidienne du coucher du soleil par Open-Meteo;
- Ctrl+C et les exceptions eteignent proprement les LED.

La version locale reste definie dans `main_tempo.py` :

```python
PROGRAM_VERSION = "3.0.0"
```

## Demarrage dans Thonny

```python
exec(open("main_tempo.py").read())
```
