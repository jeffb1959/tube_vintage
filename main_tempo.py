from machine import Pin
import neopixel
import time


VERSION = "1.0.0"
DATA_PIN = 5
LED_COUNT = 5
WARM_ORANGE = (3, 12, 0)


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

        leds = neopixel.NeoPixel(Pin(DATA_PIN, Pin.OUT), LED_COUNT)

        for index in range(LED_COUNT):
            leds[index] = WARM_ORANGE

        leds.write()
        print("Les 5 LED ont ete allumees.")

        while True:
            time.sleep_ms(1000)

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
