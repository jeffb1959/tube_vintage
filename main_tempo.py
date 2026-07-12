from machine import Pin
import config
import neopixel
import random
import time


# Informations du programme
VERSION = "1.4.0.1"

# Configuration materielle
DATA_PIN = 5
LED_COUNT = 5

# Configuration du bouton
BUTTON_PIN = 27
DEBOUNCE_MS = 50


def get_profile():
    requested_profile = getattr(config, "ACTIVE_PROFILE", "CALME")
    profiles = getattr(config, "PROFILES", {})

    if requested_profile in profiles:
        print("Profil actif :", requested_profile)
        return requested_profile, profiles[requested_profile]

    print("Profil actif inconnu :", requested_profile, "- utilisation de CALME")
    return "CALME", profiles.get("CALME", {})


def color_from_brightness(brightness, warm_orange):
    return tuple(
        max(0, min(255, component * brightness // 100))
        for component in warm_orange
    )


def turn_on(leds, brightness, warm_orange):
    # Meme couleur appliquee aux 5 LED avec une seule valeur de luminosite.
    color = color_from_brightness(brightness, warm_orange)

    for index in range(LED_COUNT):
        leds[index] = color

    leds.write()


def turn_off(leds):
    for index in range(LED_COUNT):
        leds[index] = (0, 0, 0)

    leds.write()


def pick_target_brightness(excluded_brightness, profile):
    # Force un changement de cible pour conserver une animation non bloquee.
    target = random.randint(profile["BRIGHTNESS_MIN"], profile["BRIGHTNESS_MAX"])

    if target == excluded_brightness:
        if excluded_brightness < profile["BRIGHTNESS_MAX"]:
            return excluded_brightness + 1
        return excluded_brightness - 1

    return target


def pick_transition_step(profile):
    # Rend la vitesse de chaque tube differente sans changer l'esprit du scintillement.
    transition_step = profile["TRANSITION_STEP"]

    if transition_step <= 1:
        return random.randint(1, 2)

    return random.randint(transition_step - 1, transition_step + 1)


def pick_transition_interval(profile):
    # Introduit une duree de pas propre a chaque LED et chaque changement.
    jitter = random.randint(-30, 30)
    return max(20, profile["TRANSITION_INTERVAL_MS"] + jitter)


def safe_rand(low, high):
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def make_led_state(now_ms, profile):
    current_brightness = safe_rand(
        profile["INITIAL_BRIGHTNESS"] - 6,
        profile["INITIAL_BRIGHTNESS"] + 6,
    )
    return {
        "current_brightness": current_brightness,
        "target_brightness": pick_target_brightness(
            current_brightness, profile
        ),
        "step": pick_transition_step(profile),
        "interval_ms": pick_transition_interval(profile),
        "last_transition_ms": now_ms,
        "next_target_ms": time.ticks_add(
            now_ms,
            random.randint(
                profile["TARGET_DELAY_MIN_MS"],
                profile["TARGET_DELAY_MAX_MS"],
            ),
        ),
    }


def configure_leds_for_turn_on(led_states, now_ms, profile):
    # Redemarrage doux apres un appui court sur le bouton.
    for state in led_states:
        state["current_brightness"] = safe_rand(
            profile["BRIGHTNESS_MIN"],
            profile["BRIGHTNESS_MIN"] + 5,
        )
        state["target_brightness"] = pick_target_brightness(
            state["current_brightness"], profile
        )
        state["step"] = pick_transition_step(profile)
        state["interval_ms"] = pick_transition_interval(profile)
        state["last_transition_ms"] = now_ms
        state["next_target_ms"] = time.ticks_add(
            now_ms,
            random.randint(
                profile["TARGET_DELAY_MIN_MS"],
                profile["TARGET_DELAY_MAX_MS"],
            ),
        )


def flash_color(profile):
    return tuple(
        max(0, min(255, component * profile["FLASH_INTENSITY"] // 100))
        for component in profile["FLASH_COLOR"]
    )


def plan_next_flash(now_ms, profile):
    return time.ticks_add(
        now_ms,
        random.randint(
            profile["FLASH_DELAY_MIN_MS"], profile["FLASH_DELAY_MAX_MS"]
        ),
    )


def apply_led_states(leds, led_states, flash_state, profile):
    # Appliquer l'animation normale ou remplacer une LED pendant le flash.
    for index, state in enumerate(led_states):
        if (
            flash_state["active"]
            and flash_state["led_index"] == index
        ):
            leds[index] = flash_color(profile)
        else:
            leds[index] = color_from_brightness(
                state["current_brightness"],
                profile["WARM_ORANGE"],
            )

    leds.write()


def update_animation_states(led_states, now_ms, profile):
    # Evolution progressive en douceur de chaque LED de maniere independante.
    changed = False

    for state in led_states:
        if state["current_brightness"] == state["target_brightness"]:
            if time.ticks_diff(now_ms, state["next_target_ms"]) >= 0:
                state["target_brightness"] = pick_target_brightness(
                    state["current_brightness"], profile
                )
                state["step"] = pick_transition_step(profile)
                state["interval_ms"] = pick_transition_interval(profile)
                state["last_transition_ms"] = now_ms
            continue

        if time.ticks_diff(now_ms, state["last_transition_ms"]) < state["interval_ms"]:
            continue

        if state["current_brightness"] < state["target_brightness"]:
            state["current_brightness"] = min(
                state["current_brightness"] + state["step"],
                state["target_brightness"],
            )
        else:
            state["current_brightness"] = max(
                state["current_brightness"] - state["step"],
                state["target_brightness"],
            )

        state["last_transition_ms"] = now_ms
        changed = True

        if state["current_brightness"] == state["target_brightness"]:
            state["next_target_ms"] = time.ticks_add(
                now_ms,
                random.randint(
                    profile["TARGET_DELAY_MIN_MS"],
                    profile["TARGET_DELAY_MAX_MS"],
                ),
            )

    return changed


def main():
    leds = None
    flash_state = {
        "active": False,
        "led_index": -1,
        "end_ms": 0,
        "next_ms": None,
    }

    try:
        print("Version :", VERSION)
        print("Broche DATA : GPIO", DATA_PIN)
        print("Nombre de LED :", LED_COUNT)
        print("Bouton : GPIO", BUTTON_PIN)

        profile_name, profile = get_profile()
        print("Profil visuel actif :", profile_name)

        leds = neopixel.NeoPixel(Pin(DATA_PIN, Pin.OUT), LED_COUNT)
        button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

        now_ms = time.ticks_ms()
        led_states = [make_led_state(now_ms, profile) for _ in range(LED_COUNT)]
        apply_led_states(leds, led_states, flash_state, profile)
        leds_are_on = True
        flash_state["next_ms"] = (
            plan_next_flash(now_ms, profile) if profile["FLASH_ENABLED"] else None
        )
        print("Les 5 LED ont ete allumees.")
        print(
            "Flash bleu-cyan :",
            "actif" if profile["FLASH_ENABLED"] else "desactive",
        )

        previous_button_state = button.value()
        last_button_reading = previous_button_state
        last_change_time = now_ms

        while True:
            now_ms = time.ticks_ms()
            button_reading = button.value()

            if button_reading != last_button_reading:
                last_button_reading = button_reading
                last_change_time = now_ms

            if (
                button_reading != previous_button_state
                and time.ticks_diff(now_ms, last_change_time) >= DEBOUNCE_MS
            ):
                previous_button_state = button_reading

                if previous_button_state == 0:
                    leds_are_on = not leds_are_on

                    if leds_are_on:
                        configure_leds_for_turn_on(led_states, now_ms, profile)
                        flash_state["active"] = False
                        flash_state["led_index"] = -1
                        flash_state["end_ms"] = 0
                        flash_state["next_ms"] = (
                            plan_next_flash(now_ms, profile)
                            if profile["FLASH_ENABLED"]
                            else None
                        )
                        apply_led_states(leds, led_states, flash_state, profile)
                        print("Les 5 LED ont ete allumees.")
                    else:
                        flash_state["active"] = False
                        flash_state["led_index"] = -1
                        flash_state["end_ms"] = 0
                        flash_state["next_ms"] = None
                        turn_off(leds)
                        print("Les 5 LED ont ete eteintes.")

            if leds_are_on:
                flash_updated = False

                if profile["FLASH_ENABLED"]:
                    if flash_state["active"]:
                        if time.ticks_diff(now_ms, flash_state["end_ms"]) >= 0:
                            flash_state["active"] = False
                            flash_state["led_index"] = -1
                            flash_state["end_ms"] = 0
                            flash_state["next_ms"] = plan_next_flash(now_ms, profile)
                            flash_updated = True
                    elif flash_state["next_ms"] is not None and (
                        time.ticks_diff(now_ms, flash_state["next_ms"]) >= 0
                    ):
                        flash_state["active"] = True
                        flash_state["led_index"] = random.randint(0, LED_COUNT - 1)
                        flash_state["end_ms"] = time.ticks_add(
                            now_ms, profile["FLASH_DURATION_MS"]
                        )
                        flash_updated = True
                        flash_state["next_ms"] = None
                        print(
                            "Flash discret : LED",
                            flash_state["led_index"],
                            "active",
                        )

                animation_updated = update_animation_states(led_states, now_ms, profile)
                if animation_updated or flash_updated or flash_state["active"]:
                    apply_led_states(leds, led_states, flash_state, profile)

            time.sleep_ms(profile["LOOP_DELAY_MS"])

    except KeyboardInterrupt:
        if leds is not None:
            # En cas d'interruption, annulation immediate du flash et extinction.
            flash_state["active"] = False
            flash_state["led_index"] = -1
            turn_off(leds)
            print("Les 5 LED ont ete eteintes.")

    except Exception as error:
        print("Erreur :", error)

        if leds is not None:
            try:
                flash_state["active"] = False
                flash_state["led_index"] = -1
                turn_off(leds)
                print("Les 5 LED ont ete eteintes.")
            except Exception as shutdown_error:
                print("Erreur pendant l'extinction :", shutdown_error)


main()
