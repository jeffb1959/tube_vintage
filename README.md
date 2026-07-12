# tube_vintage

## Phase 2.0.1

Cette phase ajoute une synchronisation horaire NTP en UTC, sans changer le comportement lumineux ni le bouton.

Le fichier `main_tempo.py` démarre toujours le Wi‑Fi non bloquant puis appelle `time_manager` pour synchroniser l'heure.

- synchronisation demandée peu après la connexion Wi‑Fi,
- resynchronisation automatique toutes les 6 heures,
- réessai toutes les 60 secondes en cas d'échec,
- pas de conversion de fuseau local (UTC uniquement),
- pas de dépendance externe ni de planification avancée.

L'animation, l'indicateur de profil (LED 1 à 4), le flash bleu‑cyan et `Ctrl+C` restent inchangés.

## Fichiers de la phase 2.0.1

- `wifi_secrets.py` : vos identifiants Wi‑Fi locaux.
- `wifi_secrets.example.py` : modèle sans secret à copier/modifier.
- `wifi_manager.py` : gestion Wi‑Fi non bloquante.
- `time_manager.py` : gestion NTP non bloquante (UTC).
- `.gitignore` : protège `wifi_secrets.py` des commits.

`wifi_secrets.py` ne doit jamais être envoyé sur GitHub.  
`wifi_secrets.example.py` ne contient que des valeurs fictives.

## Démarrage

1. Copier `boot.py`, `config.py`, `main_tempo.py`, `wifi_manager.py`, `time_manager.py`, `wifi_secrets.example.py` sur l'ESP32.
2. Copier `wifi_secrets.example.py` en `wifi_secrets.py` puis renseigner vos identifiants.
3. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

4. Vérifier en console :

   - `Wi-Fi : tentative de connexion ...`
   - `Wi-Fi connecté`
   - `Adresse IP : ...`
   - `NTP : synchronisation demandee`
   - `NTP : synchronisation reussie`
   - `Heure UTC : ... UTC`

5. Vérifier :

   - LED indiquant le profil au démarrage et au passage `éteint -> allumé`,
   - profil qui change correctement au rallumage,
   - bouton et `Ctrl+C` réactifs,
   - animation continue même sans Wi‑Fi.

## Détails des délais Wi‑Fi (phase 2.0.x)

- Tentatives rapides max : 5
- Délai entre tentatives rapides : 60 000 ms (1 minute)
- Délai de reconnexion longue : 21 600 000 ms (6 heures)
- Délai maximal d'une tentative individuelle : 15 000 ms

## Détails des délais NTP (phase 2.0.1)

- `NTP_POST_CONNECT_DELAY_MS = 3000` ms
- `NTP_RESYNC_INTERVAL_MS = 21600000` ms (6 heures)
- `NTP_RETRY_DELAY_MS = 60000` ms (1 minute)
- `NTP_MIN_VALID_YEAR = 2024` (validation minimale)

## Matériel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton poussoir entre `GPIO 27` et `GND` (`PULL_UP`)
- alimentation 5 V pour les LED
- résistance de 330 à 470 Ω sur la ligne DATA
- condensateur de 470 µF près de la première LED
- masse commune entre ESP32, LED et alimentation
- DATA vers `DIN` de la première LED
