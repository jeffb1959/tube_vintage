# tube_vintage

## Phase 1.1.0

Cette phase valide le fonctionnement de cinq LED WS2812 et ajoute leur commande
marche/arrêt par bouton avec un ESP32 DevKit V1 sous MicroPython. Le programme
allume les cinq LED avec une couleur orange chaude, fixe et de très faible
luminosité.

## Matériel

- ESP32 DevKit V1 alimenté par `VIN` et `GND` depuis le bus 5 V
- 5 LED WS2812 de 6 mm alimentées en 5 V
- ligne DATA connectée à `D5`, qui correspond à `GPIO 5` sur l'ESP32
- résistance de 330 à 470 ohms en série sur la ligne DATA
- condensateur de 470 µF près de la première LED
- bouton-poussoir connecté entre `GPIO 27` et `GND`
- alimentation 5 V adaptée au montage

La ligne DATA doit être raccordée à l'entrée `DIN` de la première LED. La
masse doit être commune à l'ESP32, aux LED et à l'alimentation 5 V.

Le bouton utilise la résistance interne `PULL_UP` de l'ESP32. Un appui court
éteint les LED et l'appui suivant les rallume. L'anti-rebond logiciel garantit
un seul changement d'état par appui, même si le bouton reste maintenu.

## Procédure de test

1. Vérifier le câblage, notamment DATA vers `DIN`, la polarité de
   l'alimentation et la masse commune.
2. Copier `boot.py` et `main_tempo.py` sur l'ESP32 avec l'outil MicroPython de votre
   choix.
3. Redémarrer l'ESP32 et observer la console série. Comme le fichier se nomme
   `main_tempo.py`, il ne démarre pas automatiquement au redémarrage de l'ESP32.
4. Depuis la console MicroPython de Thonny, lancer manuellement le programme
   avec :

   ```python
   exec(open("main_tempo.py").read())
   ```

5. Vérifier que les cinq LED s'allument avec un orange chaud, faible et stable.
6. Appuyer brièvement sur le bouton pour éteindre les LED, puis appuyer de
   nouveau pour les rallumer.
7. Utiliser `Ctrl+C` pour arrêter le programme : les LED sont alors éteintes
   proprement avant la fin du programme.
