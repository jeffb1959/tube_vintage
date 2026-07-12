# tube_vintage

## Phase 1.3.5

Cette phase ajoute un flash bleu-cyan léger, rare et discret, sur une seule LED à la fois.
Le scintillement principal reste indépendant par tube, lent et chaleureux, et le flash ne
remplace pas le comportement en continu.

`main_tempo.py` contient :

- la version du programme (`VERSION`),
- la configuration materielle (`DATA_PIN`, `LED_COUNT`, `BUTTON_PIN`, `DEBOUNCE_MS`),
- la logique d'animation, le bouton et la gestion propre des arrêts.

`config.py` contient les reglages visuels :

- le scintillement principal (couleur et rythme),
- le flash bleu-cyan (activation, durée, cadence et intensite).

Les valeurs visuelles personnalisees existantes restent conservees.

## Matériel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton poussoir entre `GPIO 27` et `GND` (avec `PULL_UP` interne)
- alimentation 5 V pour les LED
- resistance de 330 à 470 ohms sur la ligne DATA
- condensateur de 470 µF proche de la premiere LED
- masse commune entre ESP32, LED et alimentation
- DATA vers `DIN` de la premiere LED

## Flash bleu-cyan

- un seul tube peut flasher à la fois ;
- le tube flasher est tire au hasard ;
- la couleur de flash reste pale, douce et légèrement cyan ;
- la fréquence est rare et naturelle (plusieurs dizaines de secondes à quelques minutes).

Parametres config du flash :

- `FLASH_ENABLED`
- `FLASH_DURATION_MS`
- `FLASH_DELAY_MIN_MS`
- `FLASH_DELAY_MAX_MS`
- `FLASH_INTENSITY`
- `FLASH_COLOR`

Les nouveaux parametres sont documentés avec une valeur par defaut, minimum recommandé,
maximum recommandé et effet visuel.

## Démarrage et tests

1. Copier `boot.py`, `config.py` et `main_tempo.py` sur l'ESP32.
2. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

3. Les 5 LED gardent le scintillement indépendant orange doux.
4. Verifier qu’un flash discret peut apparaître sur une seule LED, de façon rare.
5. Un appui court eteint toutes les LED ; un appui suivant les rallume.
6. Utiliser Ctrl+C pour arrêter : les LED s’éteignent proprement.
