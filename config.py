# Valeur par defaut : (3, 12, 0)
# Minimum recommande : (0, 0, 0)
# Maximum recommande : (255, 255, 255)
# Unite : intensite de chaque composante, de 0 a 255
# Effet : definit la teinte orange de base dans l'ordre (G, R, B) observe sur
# ce montage. L'ordre RGB/GRB a deja ete corrige : augmenter G jaunit la teinte,
# augmenter R la rechauffe et augmenter B la refroidit. Ne pas permuter l'ordre.
WARM_ORANGE = (3, 12, 0)

# Valeur par defaut : 131
# Minimum recommande : 50
# Maximum recommande : 200
# Unite : pourcentage de la couleur de base
# Effet : fixe la luminosite la plus basse du scintillement sans eteindre.
BRIGHTNESS_MIN = 110

# Valeur par defaut : 193
# Minimum recommande : 75
# Maximum recommande : 255
# Unite : pourcentage de la couleur de base
# Effet : limite la luminosite la plus haute du scintillement.
BRIGHTNESS_MAX = 193

# Valeur par defaut : 175
# Minimum recommande : 50
# Maximum recommande : 255
# Unite : pourcentage de la couleur de base
# Effet : fixe la luminosite utilisee au lancement du programme.
INITIAL_BRIGHTNESS = 130

# Valeur par defaut : 1
# Minimum recommande : 1
# Maximum recommande : 5
# Unite : point de pourcentage par transition
# Effet : une petite valeur rend les variations plus progressives.
TRANSITION_STEP = 1

# Valeur par defaut : 80
# Minimum recommande : 20
# Maximum recommande : 500
# Unite : millisecondes
# Effet : regle le temps entre deux petits pas de luminosite.
TRANSITION_INTERVAL_MS = 150

# Valeur par defaut : 400
# Minimum recommande : 200
# Maximum recommande : 2000
# Unite : millisecondes
# Effet : fixe l'attente aleatoire minimale avant une nouvelle cible.
TARGET_DELAY_MIN_MS = 1000

# Valeur par defaut : 1600
# Minimum recommande : 500
# Maximum recommande : 5000
# Unite : millisecondes
# Effet : fixe l'attente aleatoire maximale avant une nouvelle cible.
TARGET_DELAY_MAX_MS = 4200

# Valeur par defaut : 10
# Minimum recommande : 5
# Maximum recommande : 50
# Unite : millisecondes
# Effet : regle la reactivite de la boucle, notamment pour le bouton.
LOOP_DELAY_MS = 10

# Valeur par defaut : True
# Minimum recommande : False
# Maximum recommande : True
# Unite : bool
# Effet : active ou desactive completement le flash bleu-cyan.
FLASH_ENABLED = True

# Valeur par defaut : 90
# Minimum recommande : 40
# Maximum recommande : 180
# Unite : millisecondes
# Effet : duree courte du flash ; trop court rend invisible, trop long devient intrusif.
FLASH_DURATION_MS = 90

# Valeur par defaut : 30000
# Minimum recommande : 10000
# Maximum recommande : 60000
# Unite : millisecondes
# Effet : attente minimum avant un nouveau flash pour garder un effet rare.
FLASH_DELAY_MIN_MS = 30000

# Valeur par defaut : 180000
# Minimum recommande : 60000
# Maximum recommande : 420000
# Unite : millisecondes
# Effet : attente maximum avant un nouveau flash pour un rythme irrégulier et naturel.
FLASH_DELAY_MAX_MS = 180000

# Valeur par defaut : 60
# Minimum recommande : 35
# Maximum recommande : 90
# Unite : pourcentage
# Effet : controle la force lumineuse du flash ; plus bas reste tres discret.
FLASH_INTENSITY = 60

# Valeur par defaut : (35, 6, 22)
# Minimum recommande : (0, 0, 0)
# Maximum recommande : (255, 255, 255)
# Unite : intensite de chaque composante, de 0 a 255 (ordre G, R, B)
# Effet : couleur bleu-cyan pale du flash, proche d'une variation de tube et non d'un flash moderne.
FLASH_COLOR = (35, 6, 22)
