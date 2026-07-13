# tube_vintage

## Phase 2.0.4.1

Cette phase conserve la securite temporelle de 72 heures tout en autorisant le
fonctionnement immediat des LED au demarrage, meme sans Wi-Fi et sans heure NTP.

Au lancement :

- le profil initial et son indication sont affiches immediatement;
- le scintillement, le flash du profil et le bouton fonctionnent normalement;
- le changement de profil reste disponible lors d'un rallumage manuel;
- les tentatives Wi-Fi et NTP continuent en arriere-plan;
- une periode de grace locale de 72 heures commence avec `ticks_ms()`.

Tant qu'aucune synchronisation NTP n'a reussi, l'horaire automatique de 06:00 a
00:00 reste desactive. Le programme fonctionne manuellement et ne tente pas de
deduire l'heure locale d'une RTC non validee.

## Premiere synchronisation et fonctionnement normal

La premiere synchronisation NTP reussie met fin a la periode de grace monotone,
enregistre le timestamp UTC et active l'horaire automatique. L'ancienne
derogation manuelle est annulee et l'etat des LED est realigne une seule fois
sur l'horaire courant, sans changer ni avancer le profil utilisateur.

Apres cette premiere synchronisation, l'age de la derniere synchronisation est
calcule avec les secondes UTC. L'horloge interne permet de conserver l'horaire,
les profils et les derogations pendant au maximum 72 heures sans nouvelle
synchronisation. `ticks_ms()` n'est alors plus la reference de cette limite.

## Verrouillage

Lorsque la periode de grace initiale expire, ou lorsque la derniere
synchronisation UTC atteint 72 heures :

- les cinq LED sont immediatement eteintes;
- le flash et l'indication de profil sont annules;
- le bouton ne peut ni rallumer les LED ni changer le profil;
- le profil utilisateur courant est conserve;
- les tentatives Wi-Fi et NTP continuent normalement.

Seule une nouvelle synchronisation NTP valide leve le verrouillage. Elle met a
jour l'etat persistant, annule toute ancienne derogation et realigne les LED sur
l'horaire avec le profil deja selectionne.

## Persistance

`time_safety.py` lit `time_state.json` au demarrage et l'ecrit uniquement apres
une synchronisation NTP reussie :

```json
{
  "version": 1,
  "last_ntp_sync_utc": 1783891200
}
```

Le fichier conserve une trace de la derniere synchronisation, mais son contenu
ne bloque pas les LED et ne sert pas a appliquer l'horaire avant qu'une heure
valide ait ete obtenue dans la session courante.

L'ecriture complete passe d'abord par `time_state.tmp`. L'ancien fichier final
est ensuite supprime avec prudence, puis le fichier temporaire est renomme en
`time_state.json`. Un fichier absent ou invalide et une erreur d'ecriture sont
geres sans interrompre les LED.

## Limite acceptee apres un redemarrage complet

La periode initiale utilise le compteur monotone de l'ESP32. Apres une coupure
complete, `ticks_ms()` repart a zero : si le Wi-Fi reste indisponible, une
nouvelle periode de grace de 72 heures commence. Cette limite est acceptee pour
ce projet, car la television est normalement alimentee en permanence. Aucun
module RTC externe ni calcul fragile du temps passe hors alimentation n'est
ajoute.

## Diagnostics acceleres

Les fonctions suivantes modifient uniquement l'etat en RAM et ne changent pas
la limite de production `72 * 60 * 60` :

```python
import time
import time_safety
import time_manager

# Avant la premiere synchronisation :
time_safety.expire_initial_grace_for_diagnostic(time.ticks_ms())

# Apres une synchronisation valide :
time_safety.simulate_sync_age_seconds(
    time_safety.MAX_TIME_WITHOUT_SYNC_SECONDS,
    time_manager.get_utc_timestamp(),
)
```

La boucle principale applique le verrouillage au passage suivant. Une nouvelle
synchronisation NTP restaure le fonctionnement normal.

## Fonctionnement conserve

- horaire automatique de 06:00 a 00:00 apres validation NTP;
- heure locale du Quebec, UTC-5 ou UTC-4 selon la saison;
- resynchronisation NTP toutes les 6 heures;
- reconnexion Wi-Fi non bloquante;
- quatre profils visuels et tous leurs parametres inchanges;
- derogation manuelle jusqu'a la prochaine transition JOUR/NUIT;
- Ctrl+C et les exceptions eteignent proprement les LED.

## Fichiers principaux

- `boot.py` : demarrage MicroPython;
- `config.py` : profils visuels et parametres d'animation;
- `main_tempo.py` : boucle principale, bouton et LED;
- `schedule_manager.py` : horaire et derogation manuelle;
- `time_manager.py` : NTP et conversion UTC vers l'heure du Quebec;
- `time_safety.py` : grace initiale, persistance et verrouillage;
- `wifi_manager.py` : connexion Wi-Fi non bloquante.

Copier aussi `time_safety.py` sur l'ESP32 lors du deploiement.

## Demarrage dans Thonny

```python
exec(open("main_tempo.py").read())
```
