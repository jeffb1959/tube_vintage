# tube_vintage

## Phase 2.0.2

Cette phase ajoute la conversion locale du QuÃ©bec depuis l'heure UTC de l'ESP32, sans changer le comportement LED ni la logique Wi-Fi.

L'horloge interne reste en UTC.
L'heure locale n'est calculÃ©e qu'au besoin, avec une rÃ¨gle de dÃ©savancement :

- heure normale : UTCâˆ’5
- heure avancÃ©e : UTCâˆ’4

La conversion utilise les rÃ¨gles rÃ©gionales suivantes :

- dÃ©but du DST : deuxiÃ¨me dimanche de mars (passage de 1Ã¨re heure vers heure avancÃ©e Ã  2:00 locale),
- fin du DST : premier dimanche de novembre (retour heure normale Ã  2:00 locale).

Aucune dÃ©cisions visuelles ne sont basÃ©es automatiquement sur l'heure dans cette phase.

## Fichiers de la phase 2.0.2

- `wifi_secrets.py` : vos identifiants Wiâ€‘Fi locaux.
- `wifi_secrets.example.py` : modÃ¨le sans secret Ã  copier/modifier.
- `wifi_manager.py` : gestion Wiâ€‘Fi non bloquante.
- `time_manager.py` : synchronisation NTP + conversion UTC vers heure locale du QuÃ©bec.
- `.gitignore` : protege `wifi_secrets.py` des commits.

`wifi_secrets.py` ne doit jamais Ãªtre envoyÃ© sur GitHub.  
`wifi_secrets.example.py` ne contient que des valeurs fictives.

## DÃ©marrage

1. Copier `boot.py`, `config.py`, `main_tempo.py`, `wifi_manager.py`, `time_manager.py`, `wifi_secrets.example.py` sur l'ESP32.
2. Copier `wifi_secrets.example.py` en `wifi_secrets.py` puis renseigner vos identifiants.
3. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

4. VÃ©rifier en console aprÃ¨s une synchronisation NTP :

   - `NTP : synchronisation demandee`
   - `NTP : synchronisation reussie`
   - `Heure UTC : YYYY-MM-DD HH:MM:SS UTC`
   - `Heure locale : YYYY-MM-DD HH:MM:SS`
   - `Mode horaire : heure avancee, UTC-4` (ou `heure normale, UTC-5`)

5. VÃ©rifier :

   - LEDs et bouton inchangés,
   - profils inchangÃ©s,
   - `Ctrl+C` rÃ©actif,
   - animation continue mÃªme sans Wiâ€‘Fi.

## MÃ©thode de diagnostic (Thonny)

Une fonction permet de vÃ©rifier une conversion UTC sans toucher Ã  l'horloge rÃ©elle :

```python
import time_manager
time_manager.debug_utc_to_local((2026, 7, 12, 21, 35, 42, 0, 0))
```

Elle affiche :

```text
Heure UTC : 2026-07-12 21:35:42 UTC
Heure locale : 2026-07-12 17:35:42
Mode horaire : heure avancee, UTC-4
```

## DÃ©lais Wiâ€‘Fi (phase 2.0.x)

- Tentatives rapides max : 5
- DÃ©lai entre tentatives rapides : 60 000 ms (1 minute)
- DÃ©lai de reconnexion longue : 21 600 000 ms (6 heures)
- DÃ©lai maximal d'une tentative individuelle : 15 000 ms

## DÃ©lais NTP (phase 2.0.2)

- `NTP_POST_CONNECT_DELAY_MS = 3000` ms
- `NTP_RESYNC_INTERVAL_MS = 21600000` ms (6 heures)
- `NTP_RETRY_DELAY_MS = 60000` ms (1 minute)
- `NTP_MIN_VALID_YEAR = 2024`

## MatÃ©riel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton poussoir entre `GPIO 27` et `GND` (`PULL_UP`)
- alimentation 5 V pour les LED
- rÃ©sistance de 330 Ã  470 Ã sur la ligne DATA
- condensateur de 470 ÂµF prÃ¨s de la premiÃ¨re LED
- masse commune entre ESP32, LED et alimentation
- DATA vers `DIN` de la premiÃ¨re LED
