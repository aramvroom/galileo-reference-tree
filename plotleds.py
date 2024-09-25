from datetime import datetime
from math import floor

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rpi_ws281x import PixelStrip, Color
import time


class LedPlot(object):
    def __init__(self, width, strip):
        self.width = width
        self.strip = strip
        self.numleds = strip.numPixels()
        self.height = self.numleds / self.width
        self.annot = [[] for _ in range(self.numleds)]
        self.leds_plot = [[] for _ in range(self.numleds)]
        self.fig, self.ax = plt.subplots()

        plt.ion()
        self.ax.set_xlim([-1, self.width])
        self.ax.set_ylim([0, (self.height + 1)*1.05])
        self.ax.set_facecolor("black")
        self.ax.set_yticklabels([])
        self.ax.set_xticklabels([])
        self.ax.set_yticks([])
        self.ax.set_xticks([])

        ledIdx: int
        for ledIdx in range(self.numleds):
            self.leds_plot[ledIdx] = plt.plot([], [], '.', markersize=20)
            Line2D.set_xdata(self.leds_plot[ledIdx][0], [ledIdx % self.width])
            Line2D.set_ydata(self.leds_plot[ledIdx][0], [self.height - floor(ledIdx / self.width)])
            self.annot[ledIdx] = self.ax.annotate('%s' % (ledIdx + 1),
                                                  xy=[ledIdx % self.width, self.height - floor(ledIdx / self.width) + 0.1],
                                                  textcoords='data', color=(1, 1, 1))

    def update_plot(self):
        plt.show()
        for ledIdx in range(self.numleds):
            red = self.strip.getPixelColorRGB(ledIdx).r / 255
            green = self.strip.getPixelColorRGB(ledIdx).g / 255
            blue = self.strip.getPixelColorRGB(ledIdx).b / 255
            max_color = max(red, green, blue)

            alpha = 1
            if max_color:
                led_brightness = max_color
                red = red / max_color           # Always make the brightest color 1 and simulate brightness through alpha
                green = green / max_color
                blue = blue / max_color
                alpha = led_brightness * self.strip.getBrightness() / 255
            Line2D.set_color(self.leds_plot[ledIdx][0], [red, green, blue, alpha])
        plt.draw()
        plt.pause(0.02)
        self.ax.set_title('Latest update %s' % datetime.utcnow().strftime('%Y/%m/%d - %H:%M:%S'))


## FUNCTIONS TO REMOVE

# Define functions which animate LEDs in various ways.
def colorWipe(ledPlot, strip, color, wait_ms=100):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        ledPlot.update_plot()

        time.sleep(wait_ms / 1000.0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbowCycle(ledPlot, strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel(
                (int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        ledPlot.update_plot()
        time.sleep(wait_ms / 1000.0)


if __name__ == '__main__':
    # LED strip configuration:
    LED_COUNT = 100  # Number of LED pixels.
    LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
    # LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10  # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    ledPlot = LedPlot(LED_COUNT, 10, strip)
    #  colorWipe(ledPlot, strip, Color(255, 255, 0))  # Red wipe
    rainbowCycle(ledPlot, strip)
