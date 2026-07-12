from machine import Pin
import config
import neopixel
import random
import time


def turn_on(leds, brightness):
    # La même couleur ajustée est envoyée aux cinq LED.
    color = tuple(
        max(0, min(255, component * brightness // 100))
        for component in config.WARM_ORANGE
    )

    for index in range(config.LED_COUNT):
        leds[index] = color

    leds.write()


def turn_off(leds):
    for index in range(config.LED_COUNT):
        leds[index] = (0, 0, 0)

    leds.write()


def main():
    leds = None

    try:
        print("Version :", config.VERSION)
        print("Broche DATA : GPIO", config.DATA_PIN)
        print("Nombre de LED :", config.LED_COUNT)
        print("Bouton : GPIO", config.BUTTON_PIN)

        leds = neopixel.NeoPixel(
            Pin(config.DATA_PIN, Pin.OUT), config.LED_COUNT
        )
        button = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_UP)

        current_brightness = config.INITIAL_BRIGHTNESS
        target_brightness = current_brightness
        turn_on(leds, current_brightness)
        leds_are_on = True
        print("Les 5 LED ont ete allumees.")

        current_time = time.ticks_ms()
        last_transition_time = current_time
        next_target_time = time.ticks_add(
            current_time,
            random.randint(config.TARGET_DELAY_MIN_MS, config.TARGET_DELAY_MAX_MS),
        )

        previous_button_state = button.value()
        last_button_reading = previous_button_state
        last_change_time = current_time

        while True:
            current_time = time.ticks_ms()
            button_reading = button.value()

            if button_reading != last_button_reading:
                last_button_reading = button_reading
                last_change_time = current_time

            if (
                button_reading != previous_button_state
                and time.ticks_diff(current_time, last_change_time)
                >= config.DEBOUNCE_MS
            ):
                previous_button_state = button_reading

                if previous_button_state == 0:
                    leds_are_on = not leds_are_on

                    if leds_are_on:
                        current_brightness = config.BRIGHTNESS_MIN
                        target_brightness = current_brightness
                        turn_on(leds, current_brightness)
                        last_transition_time = current_time
                        next_target_time = time.ticks_add(
                            current_time,
                            random.randint(
                                config.TARGET_DELAY_MIN_MS,
                                config.TARGET_DELAY_MAX_MS,
                            ),
                        )
                        print("Les 5 LED ont ete allumees.")
                    else:
                        turn_off(leds)
                        print("Les 5 LED ont ete eteintes.")

            if leds_are_on:
                if current_brightness == target_brightness:
                    if time.ticks_diff(current_time, next_target_time) >= 0:
                        target_brightness = random.randint(
                            config.BRIGHTNESS_MIN, config.BRIGHTNESS_MAX
                        )
                        last_transition_time = current_time

                        if target_brightness == current_brightness:
                            next_target_time = time.ticks_add(
                                current_time,
                                random.randint(
                                    config.TARGET_DELAY_MIN_MS,
                                    config.TARGET_DELAY_MAX_MS,
                                ),
                            )

                elif (
                    time.ticks_diff(current_time, last_transition_time)
                    >= config.TRANSITION_INTERVAL_MS
                ):
                    if current_brightness < target_brightness:
                        current_brightness = min(
                            current_brightness + config.TRANSITION_STEP,
                            target_brightness,
                        )
                    else:
                        current_brightness = max(
                            current_brightness - config.TRANSITION_STEP,
                            target_brightness,
                        )

                    turn_on(leds, current_brightness)
                    last_transition_time = current_time

                    if current_brightness == target_brightness:
                        next_target_time = time.ticks_add(
                            current_time,
                            random.randint(
                                config.TARGET_DELAY_MIN_MS,
                                config.TARGET_DELAY_MAX_MS,
                            ),
                        )

            time.sleep_ms(config.LOOP_DELAY_MS)

    except KeyboardInterrupt:
        if leds is not None:
            turn_off(leds)
            print("Les 5 LED ont ete eteintes.")

    except Exception as error:
        print("Erreur :", error)

        if leds is not None:
            try:
                turn_off(leds)
                print("Les 5 LED ont ete eteintes.")
            except Exception as shutdown_error:
                print("Erreur pendant l'extinction :", shutdown_error)


main()
