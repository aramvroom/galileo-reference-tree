import datetime
from math import pi

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class SkyPlot(object):
    def __init__(self, max_sats):
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
            self.sats_plot[satIdx] = plt.polar([], [], color='green',marker='.')
            self.annot[satIdx] = self.ax.annotate('%s' % (satIdx + 1), xy=default_coords, textcoords='data')

    def update_plot(self, ephemeris, azelev):
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
