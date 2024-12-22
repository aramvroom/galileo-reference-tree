#  Copyright (c) 2024, Aram Vroom.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.

import datetime
from math import floor

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class LedPlot(object):
    """
    Visualization class to render a graphical representation of the LED strip.

    The purpose of this class is to create a real-time visualization of the state of an
    LED strip. It is structured into a grid where each LED is represented as a dot,
    and its color and brightness correspond to its physical state.

    Attributes:
        width (int): The number of LEDs per row in the grid representation.
        strip (object): The LED strip object, assumed to have `numPixels`, `getPixelColorRGB`,
            and `getBrightness` methods.
        numleds (int): Total number of LEDs in the strip, derived from the `strip` object.
        height (int): The number of rows in the grid representation, calculated as the total number
            of LEDs divided by the width.
        annot (list[list[object]]): Storage for annotations, used to label each LED in the grid.
        leds_plot (list[list[object]]): Stores plot references for each LED dot on the visualization.
        fig (object): The `matplotlib` figure object for the visualization.
        ax (object): The `matplotlib` axes object for the visualization grid.
    """

    def __init__(self, width, strip):
        """
        This class initializes a graphical representation of a grid of LEDs using matplotlib. The
        LEDs are arranged in a 2D grid based on the given width and the total number of LEDs in
        the provided LED strip. Each LED is displayed as a dot, and its index is annotated on the
        plot.

        Parameters:
            width (int): The width of the LED grid (number of columns).
            strip (LED strip object): A LED strip object containing the LED data
        """
        self.width = width
        self.strip = strip
        self.numleds = strip.numPixels()
        self.height = self.numleds / self.width
        self.annot = [[] for _ in range(self.numleds)]
        self.leds_plot = [[] for _ in range(self.numleds)]
        self.fig, self.ax = plt.subplots()

        plt.ion()
        self.ax.set_xlim([-1, self.width])
        self.ax.set_ylim([0, (self.height + 1) * 1.05])
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
                                                  xy=[ledIdx % self.width,
                                                      self.height - floor(ledIdx / self.width) + 0.1],
                                                  textcoords='data', color=(1, 1, 1))

    def update_plot(self):
        """
        Updates the LED plot with the current RGB color and brightness values and refreshes the plot visualization.
        """
        plt.show()
        for ledIdx in range(self.numleds):
            red = self.strip.getPixelColorRGB(ledIdx).r / 255
            green = self.strip.getPixelColorRGB(ledIdx).g / 255
            blue = self.strip.getPixelColorRGB(ledIdx).b / 255
            max_color = max(red, green, blue)

            alpha = 1
            if max_color:
                led_brightness = max_color
                red = red / max_color  # Always make the brightest color 1 and plot the brightness through alpha
                green = green / max_color
                blue = blue / max_color
                alpha = led_brightness * self.strip.getBrightness() / 255
            Line2D.set_color(self.leds_plot[ledIdx][0], [red, green, blue, alpha])
        plt.draw()
        plt.pause(0.02)
        self.ax.set_title('Latest update %s' % datetime.datetime.now(datetime.UTC).strftime('%Y/%m/%d - %H:%M:%S'))
