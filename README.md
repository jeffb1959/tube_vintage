# tube_vintage

## Phase 2.0.4

Cette phase ajoute une securite temporelle aux cinq LED WS2812 de l'ESP32.

Apres une synchronisation NTP reussie, l'heure UTC de la synchronisation est
memorisee. Si le Wi-Fi ou le serveur NTP devient indisponible, l'horloge interne
continue d'alimenter l'horaire local, les profils, les animations et les
derogations du bouton pendant au maximum 72 heures.

Lorsque l'age de la derniere synchronisation atteint 72 heures :

- les cinq LED sont immediatement eteintes;
- le flash et l'indication de profil sont annules;
- le bouton ne peut ni rallumer les LED ni changer le profil;
- le profil utilisateur selectionne est conserve;
- les tentatives Wi-Fi et NTP continuent normalement.

Une nouvelle synchronisation NTP valide leve automatiquement le verrouillage.
L'ancienne derogation manuelle est annulee et les LED sont realignees sur
l'horaire courant. Si l'horaire demande l'allumage, le profil deja selectionne
est utilise et son indication habituelle est affichee, sans passer au profil
suivant.

## Persistance et redemarrage

`time_safety.py` ecrit `time_state.json` uniquement apres une synchronisation
NTP reussie. Son format est :

```json
{
  "version": 1,
  "last_ntp_sync_utc": 1783891200
}
```

L'ecriture complete est d'abord effectuee dans `time_state.tmp`. Le fichier
final precedent est ensuite supprime, puis le fichier temporaire est renomme en
`time_state.json`. Une erreur de lecture ou d'ecriture est signalee sans faire
planter les LED et sans invalider une synchronisation reussie en memoire vive.

Au lancement, le fichier persistant est lu et valide pour information, mais il
n'autorise jamais les LED. Le systeme demarre verrouille et exige une nouvelle
synchronisation NTP dans la session courante. Ce choix couvre de facon sure une
coupure complete pendant laquelle la RTC de l'ESP32 peut ne plus etre fiable.

## Test accelere de la securite

La limite de production reste toujours `72 * 60 * 60` secondes. Apres une
premiere synchronisation NTP, le diagnostic suivant simule uniquement en RAM
une synchronisation vieille de 72 heures :

```python
import time_safety
import time_manager
time_safety.simulate_sync_age_seconds(
    time_safety.MAX_TIME_WITHOUT_SYNC_SECONDS,
    time_manager.get_utc_timestamp(),
)
```

La boucle principale applique alors le verrouillage. Le fichier persistant
n'est pas modifie par ce diagnostic et la prochaine synchronisation NTP restaure
l'etat normal.

## Horaire et fonctionnement conserve

- horaire automatique de 06:00 a 00:00, heure locale du Quebec;
- conversion heure normale UTC-5 et heure avancee UTC-4;
- resynchronisation NTP toutes les 6 heures;
- reconnexion Wi-Fi non bloquante;
- quatre profils visuels inchanges;
- changement de profil uniquement au rallumage manuel autorise;
- derogation manuelle jusqu'a la prochaine transition JOUR/NUIT;
- Ctrl+C et les exceptions eteignent proprement les LED.

## Fichiers principaux

- `boot.py` : demarrage MicroPython;
- `config.py` : profils visuels et parametres d'animation;
- `main_tempo.py` : boucle principale, bouton et LED;
- `schedule_manager.py` : horaire et derogation manuelle;
- `time_manager.py` : NTP et conversion UTC vers l'heure du Quebec;
- `time_safety.py` : persistance, tolerance de 72 heures et verrouillage;
- `wifi_manager.py` : connexion Wi-Fi non bloquante.

Copier aussi `time_safety.py` sur l'ESP32 lors du deploiement. Ne pas copier un
ancien `time_state.json` pour autoriser les LED : une synchronisation NTP dans
la session reste obligatoire.

## Demarrage dans Thonny

```python
exec(open("main_tempo.py").read())
```
