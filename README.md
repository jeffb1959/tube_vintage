# tube_vintage

## Phase 1.3.0

Cette phase passe de 5 LED d'un scintillement commun a un scintillement doux et lent
propre a chaque faux tube, tout en gardant une seule couleur chaude et tres faible.
Chaque tube conserve une relation visuelle generale avec les autres, mais avec son propre
rythme.

`main_tempo.py` contient :

- la version du programme (`VERSION`),
- la configuration materielle (`DATA_PIN`, `LED_COUNT`, `BUTTON_PIN`, `DEBOUNCE_MS`),
- la logique `MicroPython` (lecture bouton, animation et arret propre).

`config.py` contient les reglages d'apparence et de rythme :

- `WARM_ORANGE`,
- `BRIGHTNESS_MIN`, `BRIGHTNESS_MAX`, `INITIAL_BRIGHTNESS`,
- `TRANSITION_STEP`, `TRANSITION_INTERVAL_MS`,
- `TARGET_DELAY_MIN_MS`, `TARGET_DELAY_MAX_MS`,
- `LOOP_DELAY_MS`.

Les valeurs personnalisées deja presentes dans `config.py` sont conservees tel que vous les
avez modifiees.

## Matériel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton pousse entre `GPIO 27` et `GND` (avec `PULL_UP` interne)
- alimentation 5 V pour les LED
- resistance de 330 à 470 ohms sur la ligne DATA
- condensateur de 470 uF proche de la premiere LED
- masse commune entre ESP32, LED et alimentation
- ligne DATA vers `DIN` de la premiere LED

## Démarrage et tests

1. Copier `boot.py`, `config.py` et `main_tempo.py` sur l'ESP32.
2. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

3. Les cinq LED s'allument en orange chaud faible, puis varient doucement selon un
   scintillement lent independant par LED.
4. Verifier que chaque LED peut suivre un rythme differents (luminosites/cibles/vitesses/delais).
5. Utiliser un appui court : un appui eteint toutes les LED, le suivant les rallume.
6. Utiliser Ctrl+C pour arreter : les LED s'eteignent proprement avant la fin du programme.
