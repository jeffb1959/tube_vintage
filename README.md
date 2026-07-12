# tube_vintage

## Phase 1.4.0.1

Cette phase ajoute un quatrième profil visuel : `NUIT`.

Le programme conserve une seule animation commune dans `main_tempo.py` et lit les valeurs du profil actif.

Le profil actif reste choisi manuellement dans `config.py` via `ACTIVE_PROFILE`.  
Le bouton reste uniquement marche/arrêt.

## Profils visuels disponibles

- `CALME`
- `VINTAGE_VIVANT`
- `USE_INSTABLE`
- `NUIT`

Le profil `NUIT` est prévu pour une pièce sombre :

- luminosité nettement réduite par rapport à `CALME`
- plage de variation plus étroite
- scintillement lent et subtil
- transitions douces
- flash bleu-cyan désactivé par défaut (`FLASH_ENABLED = False`) pour éviter un éclair visible.

Le cinquième profil est réservé à une future version `NOEL`.

## Démarrage

1. Copier `boot.py`, `config.py` et `main_tempo.py` sur l'ESP32.
2. Depuis la console MicroPython de Thonny, lancer :

   ```python
   exec(open("main_tempo.py").read())
   ```

3. Vérifier le profil actif affiché au démarrage.
4. Vérifier le scintillement visuel indépendant selon le profil choisi.
5. Vérifier que `NUIT` reste faible, lent et discret.
6. Vérifier que le bouton reste marche/arrêt.
7. Utiliser `Ctrl+C` pour arrêter : les LED s'éteignent proprement.

## Matériel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur `GPIO 5`
- bouton poussoir entre `GPIO 27` et `GND` (avec `PULL_UP` interne)
- alimentation 5 V pour les LED
- résistance de 330 à 470 Ω sur la ligne DATA
- condensateur de 470 µF près de la première LED
- masse commune entre ESP32, LED et alimentation
- ligne DATA vers `DIN` de la première LED
