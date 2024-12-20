import datetime
from math import pi

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class SkyPlot(object):
    """
    Represents a skyplot visualization of satellites.

    This class is designed to provide a sky plot representation of satellite data. It visualizes satellite positions
    on a polar graph based on their azimuth and elevation coordinates, with different colors indicating the signal health
    of each satellite. The class also offers dynamic updates to the plot.

    Attributes:
        max_sats (int): The maximum number of satellites that can be displayed on the plot.
        annot (list[list[object]]): List of annotation objects used to label satellites on the plot.
        sats_plot (list[list[matplotlib.pyplot]]): List of plots representing satellites on the polar graph.
        fig (matplotlib.figure.Figure): The matplotlib figure object for the plot.
        ax (matplotlib.axes._subplots.PolarAxesSubplot): The polar axis for the plot.
    """

    def __init__(self, max_sats):
        """
        Initializes a visualization object for satellite plotting on a polar map.

        Parameters:
            max_sats (int): Defines the maximum number of satellites that the plot will track.
        """
        self.max_sats = max_sats
        self.annot = [[] for _ in range(max_sats)]
        self.sats_plot = [[] for _ in range(max_sats)]

        plt.ion()
        self.fig, self.ax = plt.subplots(subplot_kw={'projection': 'polar'})
        self.ax.set_theta_zero_location("N")  # theta=0 at the top
        self.ax.set_theta_direction(-1)  # theta increasing clockwise
        self.ax.set_ylim([90, 0])
        self.ax.set_yticks([0, 15, 30, 45, 60, 90])

        satIdx: int
        default_coords = [-5, -5]
        for satIdx in range(max_sats):
            self.sats_plot[satIdx] = plt.polar([], [], color='green', marker='.')
            self.annot[satIdx] = self.ax.annotate('%s' % (satIdx + 1), xy=default_coords, textcoords='data')

    def update_plot(self, ephemeris, azelev):
        """
        Updates the satellite plot annotations and visualization data based on the provided ephemeris and azimuth-elevation
        data. This method adjusts the visibility, color, position, and textual annotations of satellite markers
        on the plot to reflect the current state of each satellite, depending on its visibility and signal health.

        Parameters:
            ephemeris (list[SatEphemeris]): A list where each element corresponds to an individual satellite's ephemeris data.
                Each satellite's ephemeris object should contain a 'signalHealth' attribute that determines the state
                of the satellite's signal (-1 for unknown, 0 for healthy, other values for unhealthy).
            azelev (list[list[float]]): A list of two-element lists which correspond to the azimuth and elevation data of the satellites.
                Each sublist represents a satellite, with the first element being the azimuth (in degrees) and the second
                being the elevation (in degrees). If a satellite list is empty or its elevation is negative, the satellite
                is hidden in the plot.
        """
        plt.show()
        for satIdx in range(self.max_sats):
            if len(azelev[satIdx]) and azelev[satIdx][1] < 0:
                Line2D.set_alpha(self.sats_plot[satIdx][0], 0)
                self.annot[satIdx].set_alpha(0)
            elif len(azelev[satIdx]) and azelev[satIdx][1] >= 0:
                Line2D.set_alpha(self.sats_plot[satIdx][0], 1)
                Line2D.set_xdata(self.sats_plot[satIdx][0], [azelev[satIdx][0] / 180 * pi])
                Line2D.set_ydata(self.sats_plot[satIdx][0], [azelev[satIdx][1]])
                if ephemeris[satIdx].signalHealth == 0:
                    Line2D.set_color(self.sats_plot[satIdx][0], color='green')
                elif ephemeris[satIdx].signalHealth == -1:
                    Line2D.set_color(self.sats_plot[satIdx][0], color='orange')
                else:
                    Line2D.set_color(self.sats_plot[satIdx][0], color='red')

                self.annot[satIdx].set_alpha(1)
                self.annot[satIdx].xy = [azelev[satIdx][0] / 180 * pi, azelev[satIdx][1]]
                self.annot[satIdx].set_x(azelev[satIdx][0] / 180 * pi)
                self.annot[satIdx].set_y(azelev[satIdx][1])
        plt.draw()
        plt.pause(0.02)
        self.ax.set_title('Latest update %s' % datetime.datetime.now(datetime.UTC).strftime('%Y/%m/%d - %H:%M:%S'))
