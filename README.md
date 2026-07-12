# tube_vintage

## Phase 1.0.0

Cette première phase valide le fonctionnement de cinq LED WS2812 avec un
ESP32 DevKit V1 sous MicroPython. Le programme allume les cinq LED avec une
couleur orange chaude, fixe et de très faible luminosité.

## Matériel

- ESP32 DevKit V1 alimenté par `VIN` et `GND` depuis le bus 5 V
- 5 LED WS2812 de 6 mm alimentées en 5 V
- ligne DATA connectée à `D5`, qui correspond à `GPIO 5` sur l'ESP32
- résistance de 330 à 470 ohms en série sur la ligne DATA
- condensateur de 470 µF près de la première LED
- alimentation 5 V adaptée au montage

La ligne DATA doit être raccordée à l'entrée `DIN` de la première LED. La
masse doit être commune à l'ESP32, aux LED et à l'alimentation 5 V.

Le bouton connecté à `EN` n'est pas encore utilisé par le programme.

## Procédure de test

1. Vérifier le câblage, notamment DATA vers `DIN`, la polarité de
   l'alimentation et la masse commune.
2. Copier `boot.py` et `main_tempo.py` sur l'ESP32 avec l'outil MicroPython de votre
   choix.
3. Redémarrer l'ESP32 et observer la console série. Comme le fichier se nomme
   `main_tempo.py`, il ne démarre pas automatiquement au redémarrage de l'ESP32.
4. Depuis la console MicroPython, lancer manuellement le programme avec :

   ```python
   exec(open("main_tempo.py").read())
   ```

5. Vérifier que les messages de démarrage apparaissent et que les cinq LED
   restent allumées avec un orange chaud, faible et stable.
