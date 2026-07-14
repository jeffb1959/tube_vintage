# tube_vintage

## Phase 3.0.1

Cette phase telecharge les fichiers d'une mise a jour Netlify vers des fichiers
temporaires `<nom>.new`. Aucun fichier actif n'est remplace, aucun `.bak` n'est
cree et l'ESP32 ne redemarre pas.

La version locale reste `3.0.0` dans `main_tempo.py`. Le manifeste de test
annonce `3.0.1`, ce qui permet de valider le telechargement sans inclure ni
remplacer `main_tempo.py`.

## Manifeste Netlify

`netlify/version.json` peut lister un seul fichier ou plusieurs fichiers. Seuls
les fichiers effectivement presents dans `files` sont traites. Chaque entree
exige :

- `name` : nom simple, non vide et sans chemin;
- `url` : URL HTTPS non vide;
- `size` : taille exacte, entiere et strictement positive;
- `sha256` : empreinte hexadecimale complete de 64 caracteres.

Les doublons, `..`, les chemins absolus, les barres obliques, les sous-dossiers
et les noms terminant par `.new` ou `.bak` sont refuses. Sont egalement refuses
les secrets, l'etat temporel, les marqueurs internes et les fichiers locaux npm,
Git ou VS Code, notamment :

- `wifi_secrets.py`;
- `time_state.json`;
- `.gitignore`;
- `package.json` et `package-lock.json`;
- `pyrightconfig.json`;
- `netlify.toml`.

Les fichiers `.txt` de test sont autorises. Dans une future version,
`config.py` pourra etre le seul fichier du manifeste et etre mis a jour seul.

## Telechargement en flux

`updater.py` lit chaque reponse HTTPS depuis `response.raw` par blocs de
1024 octets. Chaque bloc est immediatement :

1. ecrit dans `<nom>.new`;
2. ajoute au compteur de taille;
3. transmis au calcul SHA-256 progressif.

Le fichier complet n'est jamais charge en RAM. La reponse HTTP, le flux et le
fichier local sont fermes dans tous les chemins, puis le verrou reseau est
libere et `gc.collect()` est appele. Si la reponse MicroPython ne fournit pas de
flux brut lisible, le telechargement echoue proprement.

Avant la tentative, `os.statvfs()` est utilise lorsqu'il est disponible. La
somme des tailles annoncees et une marge de 4096 octets doivent etre libres.
Une erreur d'ecriture reste geree si cette fonction n'existe pas.

## Validation et atomicite

Apres chaque fichier, la taille recue doit correspondre exactement a `size` et
le SHA-256 calcule doit correspondre au manifeste. Un fichier valide est garde
sous son nom `.new`, sans etre charge ou importe.

La tentative est atomique pour tout le lot : si un seul fichier echoue, le
fichier incomplet et tous les `.new` deja valides pendant cette tentative sont
supprimes. Les fichiers actifs ne sont jamais touches. Une nouvelle tentative
est planifiee une heure plus tard, sans boucle rapide.

Lorsque tous les fichiers sont valides, tous les `.new` sont conserves et l'etat
RAM indique que le lot est complet. Aucune installation n'est effectuee.

## Coordination reseau et memoire

Open-Meteo garde la priorite. Netlify attend 60 secondes apres connexion et au
moins 30 secondes apres une tentative solaire. Le verrou partage
`network_request_lock.py` interdit deux requetes HTTPS simultanees et impose
10 secondes entre deux fichiers. Les diagnostics affichent la memoire libre
avant et apres chaque telechargement, le nombre total d'octets et la validation
SHA-256, sans imprimer chaque bloc.

## Fichiers de test

- `netlify/firmware/update_test_small.txt` : petit contenu reconnaissable;
- `netlify/firmware/update_test_large.txt` : fichier deterministe de 65 536
  octets pour tester le flux et la memoire.

Ces fichiers sont inertes : ils ne sont jamais importes ou executes.

## Generation locale du manifeste

Depuis Windows, a la racine du projet :

```powershell
python tools\generate_manifest.py
```

Le script recree les deux fichiers de test, calcule leur taille et leur SHA-256
par blocs, puis regenere `netlify/version.json` avec les URL du site
`tube-vintage-jeff.netlify.app`.

## Diagnostic depuis Thonny

La verification du manifeste reste forcable avec :

```python
import updater
updater.force_check()
```

Lorsqu'une version plus recente et un manifeste valide sont connus, le
telechargement est prepare automatiquement. Il peut aussi etre relance
manuellement, sans installation :

```python
updater.start_download()
```

Etat lisible du telechargement :

```python
updater.get_download_state()
```

Etat complet de l'updater :

```python
updater.get_state()
```

## Fonctionnement existant conserve

- cinq LED WS2812 sur GPIO 5 et bouton sur GPIO 27;
- quatre profils, animations et profil `NUIT` automatique;
- Wi-Fi non bloquant, NTP et heure locale du Quebec;
- horaire automatique de 06:00 a 00:00;
- securite et grace temporelles de 72 heures;
- recuperation quotidienne du coucher du soleil;
- extinction propre sur Ctrl+C et exception.

## Demarrage dans Thonny

```python
exec(open("main_tempo.py").read())
```
