from machine import Pin
import neopixel
import time


VERSION = "1.1.0"
DATA_PIN = 5
LED_COUNT = 5
BUTTON_PIN = 27
DEBOUNCE_MS = 50
POLL_DELAY_MS = 10
WARM_ORANGE = (3, 12, 0)


def turn_on(leds):
    for index in range(LED_COUNT):
        leds[index] = WARM_ORANGE

    leds.write()


def turn_off(leds):
    for index in range(LED_COUNT):
        leds[index] = (0, 0, 0)

    leds.write()


def main():
    leds = None

    try:
        print("Version :", VERSION)
        print("Broche DATA : GPIO", DATA_PIN)
        print("Nombre de LED :", LED_COUNT)
        print("Bouton : GPIO", BUTTON_PIN)

        leds = neopixel.NeoPixel(Pin(DATA_PIN, Pin.OUT), LED_COUNT)
        button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

        turn_on(leds)
        leds_are_on = True
        print("Les 5 LED ont ete allumees.")

        previous_button_state = button.value()
        last_button_reading = previous_button_state
        last_change_time = time.ticks_ms()

        while True:
            button_reading = button.value()

            if button_reading != last_button_reading:
                last_button_reading = button_reading
                last_change_time = time.ticks_ms()

            if (
                button_reading != previous_button_state
                and time.ticks_diff(time.ticks_ms(), last_change_time) >= DEBOUNCE_MS
            ):
                previous_button_state = button_reading

                if previous_button_state == 0:
                    leds_are_on = not leds_are_on

                    if leds_are_on:
                        turn_on(leds)
                        print("Les 5 LED ont ete allumees.")
                    else:
                        turn_off(leds)
                        print("Les 5 LED ont ete eteintes.")

            time.sleep_ms(POLL_DELAY_MS)

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
