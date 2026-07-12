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
