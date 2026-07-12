# ACTIVE_PROFILE choisit le jeu de constantes visuelles utilisÃƒÂ© au dÃƒÂ©marrage.
# Options disponibles : "CALME", "VINTAGE_VIVANT", "USE_INSTABLE", "NUIT".
# Si un nom invalide est saisi, le programme revient automatiquement ÃƒÂ  "CALME".
ACTIVE_PROFILE = "CALME"

# Ordre cyclique de transition entre profils lors du rallumage.
PROFILE_ORDER = (
    "CALME",
    "VINTAGE_VIVANT",
    "USE_INSTABLE",
    "NUIT",
)

# DurÃ©e de l'indication du profil au dÃ©marrage et au rallumage.
# Valeur par dÃ©faut recommandÃ©e : 1000
# Minimum recommandÃ© : 300
# Maximum recommandÃ© : 3000
# Unite : millisecondes
# Effet : affichage d'une seule LED indicatrice pendant la durÃ©e, puis retour au mode normal.
PROFILE_INDICATOR_DURATION_MS = 1000

# Chaque profil doit exposer exactement les mÃªmes clÃ©s pour garder une seule logique d'animation.
#
# CALME :
# Profil de rÃ©fÃ©rence. Il reproduit exactement le rÃ©sultat actuel aprÃ¨s les ajustements utilisateurs.
#
# VINTAGE_VIVANT :
# LÃ©gÃ¨rement plus lumineuse et plus animÃ©e que CALME, toujours sans brutalitÃ©.
#
# USE_INSTABLE :
# Variations plus prononcÃ©es et irrÃ©guliÃ¨res, avec un rendu toujours doux et non chaotique.
#
# NUIT :
# Ambiance trÃ¨s basse pour une piÃ¨ce sombre, conserve la chaleur orange et un scintillement lent.
#
# Pour ajouter un nouveau profil, dÃ©clarer un nouvel objet dans PROFILES avec les mÃªmes clÃ©s.
PROFILES = {
    "CALME": {
        # Couleur de base dans l'ordre (G, R, B) validÃ© pour ce montage.
        "WARM_ORANGE": (3, 12, 0),
        # Valeur par dÃ©faut : 131
        # Minimum recommande : 50
        # Maximum recommande : 200
        # Unite : pourcentage de la couleur de base
        # Effet : luminositÃ© minimum du scintillement sans extinction complÃ¨te.
        "BRIGHTNESS_MIN": 110,
        # Valeur par dÃ©faut : 193
        # Minimum recommande : 75
        # Maximum recommande : 255
        # Unite : pourcentage de la couleur de base
        # Effet : luminositÃ© maximum du scintillement.
        "BRIGHTNESS_MAX": 193,
        # Valeur par dÃ©faut : 175
        # Minimum recommande : 50
        # Maximum recommande : 255
        # Unite : pourcentage de la couleur de base
        # Effet : luminositÃ© de dÃ©marrage.
        "INITIAL_BRIGHTNESS": 130,
        # Valeur par dÃ©faut : 1
        # Minimum recommande : 1
        # Maximum recommande : 5
        # Unite : points de pourcentage par transition
        # Effet : pas de variation de luminositÃ© (petit pas = plus doux).
        "TRANSITION_STEP": 1,
        # Valeur par dÃ©faut : 80
        # Minimum recommande : 20
        # Maximum recommande : 500
        # Unite : millisecondes
        # Effet : rythme des mini-Ã©tapes de variation.
        "TRANSITION_INTERVAL_MS": 150,
        # Valeur par dÃ©faut : 400
        # Minimum recommande : 200
        # Maximum recommande : 2000
        # Unite : millisecondes
        # Effet : attente alÃ©atoire minimale avant une nouvelle cible.
        "TARGET_DELAY_MIN_MS": 1000,
        # Valeur par dÃ©faut : 1600
        # Minimum recommande : 500
        # Maximum recommande : 5000
        # Unite : millisecondes
        # Effet : attente alÃ©atoire maximale avant une nouvelle cible.
        "TARGET_DELAY_MAX_MS": 4200,
        # Valeur par dÃ©faut : 10
        # Minimum recommande : 5
        # Maximum recommande : 50
        # Unite : millisecondes
        # Effet : rÃ©activitÃ© de la boucle principale.
        "LOOP_DELAY_MS": 10,

        # Valeur par dÃ©faut : True
        # Minimum recommande : False
        # Maximum recommande : True
        # Unite : bool
        # Effet : active ou dÃ©sactive le flash bleu-cyan.
        "FLASH_ENABLED": True,
        # Valeur par dÃ©faut : 90
        # Minimum recommande : 40
        # Maximum recommande : 180
        # Unite : millisecondes
        # Effet : durÃ©e du flash, brÃ¨ve pour rester discret.
        "FLASH_DURATION_MS": 90,
        # Valeur par dÃ©faut : 30000
        # Minimum recommande : 10000
        # Maximum recommande : 60000
        # Unite : millisecondes
        # Effet : temps minimal entre deux flashes.
        "FLASH_DELAY_MIN_MS": 30000,
        # Valeur par dÃ©faut : 180000
        # Minimum recommande : 60000
        # Maximum recommande : 420000
        # Unite : millisecondes
        # Effet : temps maximal entre deux flashes.
        "FLASH_DELAY_MAX_MS": 180000,
        # Valeur par dÃ©faut : 60
        # Minimum recommande : 35
        # Maximum recommande : 90
        # Unite : pourcentage
        # Effet : intensitÃ© du flash, faible pour rester doux.
        "FLASH_INTENSITY": 60,
        # Valeur par dÃ©faut : (35, 6, 22)
        # Minimum recommande : (0, 0, 0)
        # Maximum recommande : (255, 255, 255)
        # Unite : intensitÃ© de chaque composante (G, R, B)
        # Effet : couleur bleu-cyan trÃ¨s douce.
        "FLASH_COLOR": (35, 6, 22),
    },
    "VINTAGE_VIVANT": {
        "WARM_ORANGE": (3, 12, 0),
        "BRIGHTNESS_MIN": 120,
        "BRIGHTNESS_MAX": 205,
        "INITIAL_BRIGHTNESS": 142,
        "TRANSITION_STEP": 2,
        "TRANSITION_INTERVAL_MS": 135,
        "TARGET_DELAY_MIN_MS": 800,
        "TARGET_DELAY_MAX_MS": 3200,
        "LOOP_DELAY_MS": 10,
        "FLASH_ENABLED": True,
        "FLASH_DURATION_MS": 110,
        "FLASH_DELAY_MIN_MS": 22000,
        "FLASH_DELAY_MAX_MS": 135000,
        "FLASH_INTENSITY": 65,
        "FLASH_COLOR": (36, 6, 24),
    },
    "USE_INSTABLE": {
        "WARM_ORANGE": (3, 12, 0),
        "BRIGHTNESS_MIN": 100,
        "BRIGHTNESS_MAX": 210,
        "INITIAL_BRIGHTNESS": 145,
        "TRANSITION_STEP": 2,
        "TRANSITION_INTERVAL_MS": 120,
        "TARGET_DELAY_MIN_MS": 650,
        "TARGET_DELAY_MAX_MS": 2800,
        "LOOP_DELAY_MS": 10,
        "FLASH_ENABLED": True,
        "FLASH_DURATION_MS": 120,
        "FLASH_DELAY_MIN_MS": 15000,
        "FLASH_DELAY_MAX_MS": 90000,
        "FLASH_INTENSITY": 68,
        "FLASH_COLOR": (38, 7, 25),
    },
    "NUIT": {
        "WARM_ORANGE": (3, 12, 0),
        "BRIGHTNESS_MIN": 72,
        "BRIGHTNESS_MAX": 110,
        "INITIAL_BRIGHTNESS": 90,
        "TRANSITION_STEP": 1,
        "TRANSITION_INTERVAL_MS": 170,
        "TARGET_DELAY_MIN_MS": 1400,
        "TARGET_DELAY_MAX_MS": 5000,
        "LOOP_DELAY_MS": 10,
        "FLASH_ENABLED": False,
        "FLASH_DURATION_MS": 0,
        "FLASH_DELAY_MIN_MS": 3600000,
        "FLASH_DELAY_MAX_MS": 3600000,
        "FLASH_INTENSITY": 0,
        "FLASH_COLOR": (35, 6, 22),
    },
}

# Le cinquiÃ¨me profil est rÃ©servÃ© pour une future version "NOEL".
