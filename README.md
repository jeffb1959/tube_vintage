# tube_vintage

## Phase 1.4.2

Le démarrage affiche une **indication courte du profil actif**, puis repasse au scintillement normal des 5 LED.

Les profils disponibles sont :

1. `CALME` → LED 1
2. `VINTAGE_VIVANT` → LED 2
3. `USE_INSTABLE` → LED 3
4. `NUIT` → LED 4

La LED 5 reste réservée au futur profil `NOEL`.

Ordre cyclique des profils :

1. `CALME`
2. `VINTAGE_VIVANT`
3. `USE_INSTABLE`
4. `NUIT`

Lancement : `ACTIVE_PROFILE` dans `config.py` reste le profil initial au démarrage.

- au démarrage de `main_tempo.py`, le profil actif s'affiche d'abord sur une seule LED (sans couleur spéciale), puis les 5 LED passent à l'animation du profil ;
- à chaque passage `éteint -> allumé` (bouton), le nouveau profil est d'abord indiqué puis l'affichage normal reprend ;
- `CTRL+C` demeure réactif et éteint immédiatement les LED ;
- le bouton reste réactif pendant la phase d'indication.

Paramètre ajustable dans `config.py` :

- `PROFILE_INDICATOR_DURATION_MS` (durée d'indication en ms)

## Démarrage

1. Copier `boot.py`, `config.py` et `main_tempo.py` sur l'ESP32.
2. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

3. Vérifier la séquence au démarrage et au rallumage :
   - LED 1 allumée brièvement pour `CALME`,
   - LED 2 pour `VINTAGE_VIVANT`,
   - LED 3 pour `USE_INSTABLE`,
   - LED 4 pour `NUIT`.

4. Vérifier l'allumage/arrêt par le bouton :
   - LED éteintes -> appui court : rallume et indique le profil actif,
   - LED allumées -> appui court : éteint.

5. Vérifier le cycle de profils :
   `CALME -> VINTAGE_VIVANT -> USE_INSTABLE -> NUIT -> CALME`.

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
