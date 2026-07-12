# tube_vintage

## Phase 2.0.3.1

Objectif de cette phase : ajouter les minutes a l'horaire automatique tout en conservant le comportement valide.

- Les LEDs s'allument a 06:00.
- Les LEDs s'eteignent a 00:00.
- Horaire actif uniquement avec une heure locale valide (`time_manager.py`).
- Tant que l'heure n'est pas valide, le fonctionnement reste manuel.
- Comparaison basee sur les minutes depuis minuit :
  - `minutes_courantes = heure * 60 + minute`
  - `minutes_debut = heure_debut * 60 + minute_debut`
  - `minutes_fin = heure_fin * 60 + minute_fin`

Le bouton garde une priorite temporaire :

- un appui qui eteint cree une derogation manuelle jusqu'a la prochaine transition JOUR/NUIT;
- un appui qui rallume cree une derogation manuelle jusqu'a la prochaine transition JOUR/NUIT.

Au passage, la derogation est annulee et l'horaire reprend le controle.

Comportement conserve :

- changement de profil au rallumage manuel (et seulement alors)
- indication par LED au rallumage (profil actif)
- scintillement et flash bleu-cyan inchanges
- Ctrl+C eteint proprement
- extinction de securite en cas d'exception

Regles de cette phase :

- aucune sauvegarde persistante (ni dernier etat, ni derogation)
- pas de securite de 72h pour cette phase

## Fichiers de la phase 2.0.3.1

- `boot.py` : demarrage MicroPython.
- `config.py` : profils visuels et parametres d'animation.
- `main_tempo.py` : logique principale (version, branchements, bouton, LEDs).
- `schedule_manager.py` : gestion technique de l'horaire 06:00-00:00 et derogation.
- `wifi_manager.py` : gestion Wi-Fi non bloquante.
- `time_manager.py` : synchronisation NTP + conversion UTC -> heure locale du Quebec.
- `wifi_secrets.example.py` : modele d'identifiants Wi-Fi (a copier en `wifi_secrets.py`).
- `wifi_secrets.py` : identifiants Wi-Fi locaux (a exclure du depot).
- `.gitignore` : protege `wifi_secrets.py`.

## Demarrage

1. Copier sur l'ESP32 : `boot.py`, `config.py`, `main_tempo.py`, `schedule_manager.py`, `wifi_manager.py`, `time_manager.py`, `wifi_secrets.example.py`.
2. Copier `wifi_secrets.example.py` en `wifi_secrets.py`.
3. Depuis la console Thonny :

   ```python
   exec(open("main_tempo.py").read())
   ```

## Messages console

- `Version : 2.0.3` (main_tempo.py)
- `Phase : 2.0.3.1`
- `Horaire : periode JOUR` ou `Horaire : periode NUIT`
- `Horaire : allumage automatique` ou `Horaire : extinction automatique`
- `Horaire : derogation manuelle active jusqu'a la prochaine transition`
- `Horaire : derogation manuelle annulee`

## Test court (facultatif, a retirer ensuite)

Pour verifier rapidement la transition:

```python
SCHEDULE_START_HOUR = 17
SCHEDULE_START_MINUTE = 25
SCHEDULE_END_HOUR = 17
SCHEDULE_END_MINUTE = 26
```

Attendu:

- allumage automatique a 17:25
- extinction automatique a 17:26

Puis reinstaller les valeurs normales:

```python
SCHEDULE_START_HOUR = 6
SCHEDULE_START_MINUTE = 0
SCHEDULE_END_HOUR = 0
SCHEDULE_END_MINUTE = 0
```

## Materiel

- ESP32 DevKit V1
- 5 LED WS2812 de 6 mm sur GPIO 5
- bouton poussoir entre GPIO 27 et GND (PULL_UP)
- alimentation 5V pour les LED
- resistance 330-470 ohms sur la ligne DATA
- condensateur 470 uF pres de la premiere LED
- masse commune ESP32 / LED / alimentation
- DATA vers DIN de la premiere LED
