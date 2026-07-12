# tube_vintage

## Phase 1.4.1

Le bouton change maintenant le profil visuel uniquement à la relance des LED.

Ordre cyclique des profils :

1. `CALME`
2. `VINTAGE_VIVANT`
3. `USE_INSTABLE`
4. `NUIT`

Lancement : `ACTIVE_PROFILE` dans `config.py` reste le profil initial au démarrage.

- bouton appui lorsque LED allumées -> LED éteintes
- bouton appui lorsque LED éteintes -> profil suivant puis LED allumées

Le profil ne change que sur cette transition `éteint -> allumé`.  
Aucune persistance de profil n’est faite pour l’instant.

L’indication visuelle du profil par LED est prévue en phase 1.4.2.

## Démarrage

1. Copier `boot.py`, `config.py` et `main_tempo.py` sur l'ESP32.
2. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

3. Vérifier le profil initial affiché au démarrage.
4. Vérifier la séquence de bouton : éteindre puis rallumer pour changer de profil.
5. Vérifier le cycle `CALME -> VINTAGE_VIVANT -> USE_INSTABLE -> NUIT -> CALME`.
6. Vérifier `Ctrl+C` : extinction propre.

## Matériel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton poussoir entre `GPIO 27` et `GND` (`PULL_UP`)
- alimentation 5 V pour les LED
- résistance de 330 à 470 Ω sur la ligne DATA
- condensateur de 470 µF près de la première LED
- masse commune entre ESP32, LED et alimentation
- DATA vers `DIN` de la première LED
