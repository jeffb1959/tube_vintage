# tube_vintage

## Phase 1.2.1

Cette phase valide le fonctionnement de cinq LED WS2812 et ajoute leur commande
marche/arrêt par bouton avec un ESP32 DevKit V1 sous MicroPython. Les cinq LED
produisent maintenant ensemble un scintillement orange doux, lent et irrégulier,
à très faible luminosité. L'animation indépendante de chaque tube viendra dans
une phase suivante.

La luminosité a été augmentée de 75 % par rapport à la phase 1.2.0, tout en
conservant la même teinte et la même amplitude relative de scintillement.

## Structure du projet

- `boot.py` affiche le message de démarrage MicroPython ;
- `main_tempo.py` contient la logique du programme lancé manuellement ;
- `config.py` centralise les réglages matériels, visuels et temporels.

Dans `config.py`, chaque paramètre indique sa valeur par défaut, sa plage
recommandée, son unité lorsqu'elle existe et son effet. Les réglages peuvent
ainsi être ajustés sans modifier la logique de `main_tempo.py`.

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

## Réglage du scintillement

Les principales constantes de `config.py` permettent d'ajuster l'effet :

- `BRIGHTNESS_MIN` et `BRIGHTNESS_MAX` limitent la petite plage de luminosité ;
- `TRANSITION_STEP` et `TRANSITION_INTERVAL_MS` règlent la douceur et la vitesse
  des transitions ;
- `TARGET_DELAY_MIN_MS` et `TARGET_DELAY_MAX_MS` définissent l'attente variable
  entre deux cibles ;
- `LOOP_DELAY_MS` règle la courte temporisation de la boucle principale.

## Procédure de test

1. Vérifier le câblage, notamment DATA vers `DIN`, la polarité de
   l'alimentation et la masse commune.
2. Copier `boot.py`, `config.py` et `main_tempo.py` sur l'ESP32 avec l'outil
   MicroPython de votre choix.
3. Redémarrer l'ESP32 et observer la console série. Comme le fichier se nomme
   `main_tempo.py`, il ne démarre pas automatiquement au redémarrage de l'ESP32.
4. Depuis la console MicroPython de Thonny, lancer manuellement le programme
   avec :

   ```python
   exec(open("main_tempo.py").read())
   ```

5. Vérifier que les cinq LED s'allument avec un orange chaud et varient toutes
   ensemble de façon lente, douce et irrégulière.
6. Appuyer brièvement sur le bouton pour éteindre les LED, puis appuyer de
   nouveau pour les rallumer.
7. Utiliser `Ctrl+C` pour arrêter le programme : les LED sont alors éteintes
   proprement avant la fin du programme.
