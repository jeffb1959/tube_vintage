# tube_vintage

## Correction 3.0.1.3

Les fichiers OTA ne sont plus telecharges dans la boucle complete de
`main_tempo.py`. Lorsque `updater.py` detecte une version distante superieure,
l'application sauvegarde le profil utilisateur, cree un marqueur persistant,
eteint les LED et redemarre vers un environnement OTA minimal.

Aucun fichier actif n'est remplace, aucun `.bak` n'est cree et aucun fichier
`.new` n'est installe dans cette phase.

## Profil utilisateur persistant

Avant le redemarrage OTA, `runtime_state.py` ecrit atomiquement
`runtime_state.json` via `runtime_state.tmp` :

```json
{
  "version": 1,
  "user_profile": "CALME"
}
```

La valeur sauvegardee est toujours le vrai profil choisi avec le bouton, meme
si le profil effectif est temporairement `NUIT`. Au prochain lancement manuel
de `main_tempo.py`, le profil est restaure s'il existe encore dans
`config.PROFILES`; sinon le profil par defaut de `config.py` est utilise.

## Marqueur OTA

`updater.py` valide le manifeste, mais ne telecharge plus ses fichiers. Il cree
atomiquement `ota_download_pending.json` via `ota_download_pending.tmp` :

```json
{
  "version": 1,
  "remote_version": "3.0.6",
  "files": [
    {
      "name": "update_test_small.txt",
      "url": "https://example.netlify.app/firmware/update_test_small.txt",
      "size": 47,
      "sha256": "empreinte-hexadecimale-de-64-caracteres"
    }
  ],
  "attempts": 0
}
```

Le marqueur contient toutes les donnees necessaires au telechargeur minimal. Il
est revalide apres redemarrage : noms simples sans chemin, URL HTTPS, taille
positive, SHA-256 complet et absence de doublons.

## Selection au demarrage

`boot.py` cherche uniquement le marqueur OTA :

- s'il existe, `ota_downloader.py` est importe et execute;
- sinon, le demarrage de developpement actuel est conserve et
  `main_tempo.py` n'est pas lance automatiquement.

Le mode minimal n'importe ni l'application LED, ni les profils, ni l'horaire,
ni NTP, ni Open-Meteo, ni la logique nocturne. Il charge seulement le Wi-Fi, les
secrets locaux, HTTP, SHA-256 et les petits modules d'etat OTA.

## Telechargement minimal

`ota_downloader.py` reutilise la methode validee par le test de vitesse :

- bloc de 1024 octets;
- tampon unique et `readinto()` prioritaire;
- repli sur `read()`;
- `Accept-Encoding: identity` et `Connection: close`;
- arret exact a la taille annoncee, sans lecture d'EOF supplementaire;
- ecriture `.new` et SHA-256 progressifs;
- progression console tous les 16 Kio;
- fermeture systematique et `gc.collect()`.

Tous les fichiers doivent etre valides. Une seule erreur supprime tous les
`.new` du lot. En cas de succes, les `.new` sont conserves et le marqueur
atomique `ota_download_ready.json` contient :

```json
{
  "version": 1,
  "remote_version": "3.0.6",
  "files": [
    "update_test_small.txt.new",
    "update_test_large.txt.new"
  ]
}
```

Le marqueur en attente est alors supprime et l'ESP32 redemarre. Aucune
installation n'est effectuee.

## Limite d'echecs

Le compteur `attempts` est incremente atomiquement avant chaque tentative. Une
erreur nettoie tous les `.new`, conserve une erreur courte et redemarre pour un
nouvel essai. Apres trois echecs, le marqueur en attente est supprime et le
systeme revient au demarrage normal, sans installation et sans boucle infinie.

## Fichiers toujours exclus des mises a jour

- `wifi_secrets.py`;
- `time_state.json` et `time_state.tmp`;
- `runtime_state.json` et `runtime_state.tmp`;
- `ota_download_pending.json` et son temporaire;
- `ota_download_ready.json` et son temporaire;
- tous les `.new` et `.bak`;
- les marqueurs internes, fichiers npm, Git, VS Code et outils locaux.

## Fonctionnement conserve

La version locale reste `3.0.0`. Les profils, valeurs visuelles, bouton,
horaire 06:00-00:00, Wi-Fi, NTP, securite temporelle, Open-Meteo et profil
`NUIT` automatique ne sont pas modifies.

## Lancement de developpement dans Thonny

```python
exec(open("main_tempo.py").read())
```
