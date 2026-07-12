# tube_vintage

## Phase 2.0.0

Cette phase ajoute la connexion Wi‑Fi de manière non bloquante, sans modifier l’animation, le bouton ou les profils visuels.

Le fichier `main_tempo.py` démarre avec la phase Wi‑Fi active et appelle régulièrement un gestionnaire dédié.

- démarrage d’une tentative immédiate de connexion,
- en cas d’échec : 5 tentatives rapides (1 minute d’intervalle chacune),
- puis une stratégie longue : une tentative toutes les 6 heures.

L’indication de profil (LED 1 à 4) et toutes les animations restent inchangées.

## Fichiers créés pour la phase 2.0.0

- `wifi_secrets.py` : vos identifiants Wi‑Fi locaux.
- `wifi_secrets.example.py` : modèle sans secret à copier/modifier.
- `wifi_manager.py` : module dédié à la gestion Wi‑Fi non bloquante.
- `.gitignore` : protège `wifi_secrets.py` des commits.

`wifi_secrets.py` ne doit jamais être envoyé sur GitHub.  
`wifi_secrets.example.py` ne contient que des valeurs fictives.

## Démarrage

1. Copier `boot.py`, `config.py`, `main_tempo.py`, `wifi_manager.py`, `wifi_secrets.example.py` sur l’ESP32.
2. Copier `wifi_secrets.example.py` en `wifi_secrets.py` puis renseigner vos identifiants.
3. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

4. Vérifier en console :

   - `Wi-Fi : tentative de connexion ...`
   - `Wi-Fi connecté`
   - `Adresse IP : ...`

5. Vérifier :

   - LED indiquant le profil au démarrage et au passage `éteint -> allumé`,
   - cycle des profils au rallumage,
   - bouton et `Ctrl+C` toujours réactifs,
   - LED continue à fonctionner même sans Wi‑Fi.

## Comportement Wi‑Fi attendu

- Aucun blocage de la boucle principale (pas de `sleep` longs).
- Une seule tentative active à la fois.
- `wifi_secrets.py` manquant/incorrect : message clair, animation et bouton restent actifs.
- Pas de NTP, pas d’API, pas d’horloge ni de planification horaire dans cette phase.

## Détails des délais

- Tentatives rapides max : 5
- Délai entre tentatives rapides : 60 000 ms (1 minute)
- Délai de reconnexion longue : 21 600 000 ms (6 heures)
- Délai maximal d’une tentative individuelle : 15 000 ms

## Matériel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton poussoir entre `GPIO 27` et `GND` (`PULL_UP`)
- alimentation 5 V pour les LED
- résistance de 330 à 470 Ω sur la ligne DATA
- condensateur de 470 µF près de la première LED
- masse commune entre ESP32, LED et alimentation
- DATA vers `DIN` de la première LED

