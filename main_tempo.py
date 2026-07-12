from machine import Pin
import config
import wifi_manager
import neopixel
import random
import time
import time_manager
import schedule_manager


# Informations du programme
VERSION = "2.0.3"

# Configuration materielle
DATA_PIN = 5
LED_COUNT = 5

# Configuration du bouton
BUTTON_PIN = 27
DEBOUNCE_MS = 50


def get_profile_order():
    profile_order = getattr(config, "PROFILE_ORDER", tuple(config.PROFILES.keys()))
    filtered_order = [name for name in profile_order if name in config.PROFILES]

    if not filtered_order:
        return ("CALME",)

    return tuple(filtered_order)


def resolve_profile(requested_profile):
    profile_order = get_profile_order()

    if requested_profile in config.PROFILES and requested_profile in profile_order:
        return requested_profile

    fallback = profile_order[0] if profile_order else "CALME"

    if requested_profile not in config.PROFILES:
        print("Profil inconnu :", requested_profile, "- retour a", fallback)
    elif requested_profile not in profile_order:
        print(
            "Profil non present dans PROFILE_ORDER :",
            requested_profile,
            "- retour a",
            fallback,
        )

    return fallback


def get_initial_profile():
    requested_profile = getattr(config, "ACTIVE_PROFILE", "CALME")
    profile_name = resolve_profile(requested_profile)
    return profile_name, config.PROFILES[profile_name]


def next_profile_name(current_profile_name, profile_order):
    if current_profile_name not in profile_order:
        return profile_order[0]

    current_index = profile_order.index(current_profile_name)
    return profile_order[(current_index + 1) % len(profile_order)]


def load_profile(profile_name):
    return config.PROFILES[profile_name]


def color_from_brightness(brightness, warm_orange):
    return tuple(
        max(0, min(255, component * brightness // 100))
        for component in warm_orange
    )


def turn_off(leds):
    for index in range(LED_COUNT):
        leds[index] = (0, 0, 0)

    leds.write()


def pick_target_brightness(excluded_brightness, profile):
    target = random.randint(profile["BRIGHTNESS_MIN"], profile["BRIGHTNESS_MAX"])

    if target == excluded_brightness:
        if excluded_brightness < profile["BRIGHTNESS_MAX"]:
            return excluded_brightness + 1
        return excluded_brightness - 1

    return target


def pick_transition_step(profile):
    transition_step = profile["TRANSITION_STEP"]

    if transition_step <= 1:
        return random.randint(1, 2)

    return random.randint(transition_step - 1, transition_step + 1)


def pick_transition_interval(profile):
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
        "target_brightness": pick_target_brightness(current_brightness, profile),
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


def get_indicator_led_index(profile_name):
    return {
        "CALME": 0,
        "VINTAGE_VIVANT": 1,
        "USE_INSTABLE": 2,
        "NUIT": 3,
    }.get(profile_name, -1)


def start_profile_indicator(indicator_state, profile_name, now_ms):
    indicator_state["led_index"] = get_indicator_led_index(profile_name)
    indicator_state["active"] = indicator_state["led_index"] >= 0

    if indicator_state["active"]:
        indicator_state["end_ms"] = time.ticks_add(
            now_ms,
            config.PROFILE_INDICATOR_DURATION_MS,
        )
    else:
        indicator_state["end_ms"] = 0


def stop_profile_indicator(indicator_state):
    indicator_state["active"] = False
    indicator_state["led_index"] = -1
    indicator_state["end_ms"] = 0


def apply_profile_indicator(leds, led_states, indicator_state, profile):
    indicator_led = indicator_state["led_index"]
    indicator_color = color_from_brightness(
        led_states[indicator_led]["current_brightness"],
        profile["WARM_ORANGE"],
    )

    for index in range(LED_COUNT):
        if index == indicator_led:
            leds[index] = indicator_color
        else:
            leds[index] = (0, 0, 0)

    leds.write()


def configure_leds_for_turn_on(led_states, now_ms, profile):
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
    if not profile["FLASH_ENABLED"]:
        return None

    return time.ticks_add(
        now_ms,
        random.randint(
            profile["FLASH_DELAY_MIN_MS"],
            profile["FLASH_DELAY_MAX_MS"],
        ),
    )


def apply_led_states(leds, led_states, flash_state, profile):
    for index, state in enumerate(led_states):
        if flash_state["active"] and flash_state["led_index"] == index:
            leds[index] = flash_color(profile)
        else:
            leds[index] = color_from_brightness(
                state["current_brightness"],
                profile["WARM_ORANGE"],
            )

    leds.write()


def update_animation_states(led_states, now_ms, profile):
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


def load_next_profile(current_profile_name, profile_order, led_states, now_ms, flash_state):
    new_profile_name = next_profile_name(current_profile_name, profile_order)
    new_profile = load_profile(new_profile_name)

    flash_state["active"] = False
    flash_state["led_index"] = -1
    flash_state["end_ms"] = 0

    configure_leds_for_turn_on(led_states, now_ms, new_profile)
    flash_state["next_ms"] = plan_next_flash(now_ms, new_profile)
    return new_profile_name, new_profile


def apply_manual_on(
    leds, led_states, flash_state, indicator_state, profile_name, profile, now_ms
):
    print("Profil selectionne :", profile_name)
    start_profile_indicator(indicator_state, profile_name, now_ms)

    if indicator_state["active"]:
        print("Indication : LED", indicator_state["led_index"] + 1)
        apply_profile_indicator(leds, led_states, indicator_state, profile)
    else:
        apply_led_states(leds, led_states, flash_state, profile)

    print("LEDs allumees")


def apply_manual_off(leds, flash_state, indicator_state):
    stop_profile_indicator(indicator_state)
    flash_state["active"] = False
    flash_state["led_index"] = -1
    flash_state["end_ms"] = 0
    flash_state["next_ms"] = None
    turn_off(leds)
    print("LEDs eteintes")


def apply_auto_on(leds, led_states, flash_state, indicator_state, profile_name, profile, now_ms):
    flash_state["active"] = False
    flash_state["led_index"] = -1
    flash_state["end_ms"] = 0
    flash_state["next_ms"] = plan_next_flash(now_ms, profile)
    configure_leds_for_turn_on(led_states, now_ms, profile)
    start_profile_indicator(indicator_state, profile_name, now_ms)
    print("Profil selectionne :", profile_name)

    if indicator_state["active"]:
        print("Indication : LED", indicator_state["led_index"] + 1)
        apply_profile_indicator(leds, led_states, indicator_state, profile)
    else:
        apply_led_states(leds, led_states, flash_state, profile)

    print("LEDs allumees")


def apply_auto_off(leds, flash_state, indicator_state):
    stop_profile_indicator(indicator_state)
    flash_state["active"] = False
    flash_state["led_index"] = -1
    flash_state["end_ms"] = 0
    flash_state["next_ms"] = None
    turn_off(leds)
    print("LEDs eteintes")


def print_local_time(local_time):
    if local_time is None:
        return

    timezone_mode = time_manager.get_timezone_mode_label()
    print("Heure locale : " + time_manager.format_time_tuple(local_time))
    print("Mode horaire : " + timezone_mode)


def main():
    leds = None
    flash_state = {
        "active": False,
        "led_index": -1,
        "end_ms": 0,
        "next_ms": None,
    }
    indicator_state = {
        "active": False,
        "led_index": -1,
        "end_ms": 0,
    }

    try:
        print("Version :", VERSION)
        print("Phase : 2.0.3")
        print("Broche DATA : GPIO", DATA_PIN)
        print("Nombre de LED :", LED_COUNT)
        print("Bouton : GPIO", BUTTON_PIN)

        profile_order = get_profile_order()
        profile_name, profile = get_initial_profile()

        print("Profil visuel actif :", profile_name)

        leds = neopixel.NeoPixel(Pin(DATA_PIN, Pin.OUT), LED_COUNT)
        button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

        now_ms = time.ticks_ms()
        wifi_manager.initialize()
        time_manager.initialize()
        schedule_manager.initialize()
        led_states = [make_led_state(now_ms, profile) for _ in range(LED_COUNT)]
        flash_state["next_ms"] = plan_next_flash(now_ms, profile)

        start_profile_indicator(indicator_state, profile_name, now_ms)

        leds_are_on = True
        print("LEDs allumees")
        print("Profil selectionne :", profile_name)

        if indicator_state["active"]:
            print("Indication : LED", indicator_state["led_index"] + 1)
            apply_profile_indicator(leds, led_states, indicator_state, profile)
        else:
            apply_led_states(leds, led_states, flash_state, profile)

        previous_button_state = button.value()
        last_button_reading = previous_button_state
        last_change_time = now_ms

        while True:
            now_ms = time.ticks_ms()
            wifi_manager.update(now_ms)
            synced = time_manager.update(
                now_ms, wifi_connected=wifi_manager.is_connected()
            )

            local_time = None
            if time_manager.is_time_valid():
                local_time = time_manager.get_local_time()
                if synced:
                    print_local_time(local_time)

            schedule_event = schedule_manager.update(
                local_time,
                time_manager.is_time_valid(),
                leds_are_on,
            )

            if schedule_event is not None and schedule_event["changed"]:
                if schedule_event["manual_override_cleared"]:
                    print("Horaire : derogation manuelle annulee")

                if schedule_event["message"] is not None:
                    print(schedule_event["message"])
                print(
                    "Horaire : "
                    + (
                        "allumage automatique"
                        if schedule_event["state_on"]
                        else "extinction automatique"
                    )
                )

                leds_are_on = schedule_event["state_on"]
                if leds_are_on:
                    apply_auto_on(
                        leds,
                        led_states,
                        flash_state,
                        indicator_state,
                        profile_name,
                        profile,
                        now_ms,
                    )
                else:
                    apply_auto_off(leds, flash_state, indicator_state)

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

                    if not leds_are_on:
                        schedule_manager.set_manual_override(False)
                        print(
                            "Horaire : derogation manuelle active jusqu'a la prochaine transition"
                        )
                        apply_manual_off(leds, flash_state, indicator_state)
                    else:
                        schedule_manager.set_manual_override(True)
                        print(
                            "Horaire : derogation manuelle active jusqu'a la prochaine transition"
                        )
                        profile_name, profile = load_next_profile(
                            profile_name, profile_order, led_states, now_ms, flash_state
                        )
                        apply_manual_on(
                            leds,
                            led_states,
                            flash_state,
                            indicator_state,
                            profile_name,
                            profile,
                            now_ms,
                        )

            if leds_are_on:
                animation_updated = False
                flash_updated = False

                if indicator_state["active"]:
                    if time.ticks_diff(now_ms, indicator_state["end_ms"]) >= 0:
                        stop_profile_indicator(indicator_state)

                        if (
                            flash_state["next_ms"] is not None
                            and time.ticks_diff(now_ms, flash_state["next_ms"]) >= 0
                        ):
                            flash_state["next_ms"] = plan_next_flash(now_ms, profile)

                        apply_led_states(leds, led_states, flash_state, profile)
                    else:
                        animation_updated = update_animation_states(
                            led_states, now_ms, profile
                        )
                        if animation_updated:
                            apply_profile_indicator(
                                leds,
                                led_states,
                                indicator_state,
                                profile,
                            )
                else:
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
                                now_ms,
                                profile["FLASH_DURATION_MS"],
                            )
                            flash_state["next_ms"] = None
                            flash_updated = True

                    animation_updated = update_animation_states(
                        led_states, now_ms, profile
                    )
                    if animation_updated or flash_updated or flash_state["active"]:
                        apply_led_states(leds, led_states, flash_state, profile)

            time.sleep_ms(profile["LOOP_DELAY_MS"])

    except KeyboardInterrupt:
        if leds is not None:
            flash_state["active"] = False
            flash_state["led_index"] = -1
            stop_profile_indicator(indicator_state)
            turn_off(leds)
            print("LEDs eteintes")

    except Exception as error:
        print("Erreur :", error)

        if leds is not None:
            try:
                flash_state["active"] = False
                flash_state["led_index"] = -1
                stop_profile_indicator(indicator_state)
                turn_off(leds)
                print("LEDs eteintes")
            except Exception as shutdown_error:
                print("Erreur pendant l'extinction :", shutdown_error)


main()
