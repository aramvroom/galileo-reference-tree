import unittest
from unittest.mock import patch, MagicMock
from gnss_monitor.skyplot import *  # Assuming SkyPlot is in a file named sky_plot.py

class TestSkyPlot(unittest.TestCase):

    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.ion')
    def test_initialization(self, mock_ion, mock_subplots):
        mock_ax = MagicMock()
        mock_fig = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        max_sats = 5
        plot = SkyPlot(max_sats)

        # Test that max_sats, annot, and sats_plot are initialized correctly
        self.assertEqual(plot.max_sats, max_sats)
        self.assertEqual(len(plot.annot), max_sats)
        self.assertEqual(len(plot.sats_plot), max_sats)

        # Check that the polar plot setup is correct
        mock_subplots.assert_called_once_with(subplot_kw={'projection': 'polar'})
        mock_ax.set_theta_zero_location.assert_called_with("N")
        mock_ax.set_theta_direction.assert_called_with(-1)
        mock_ax.set_ylim.assert_called_with([90, 0])
        mock_ax.set_yticks.assert_called_with([0, 15, 30, 45, 60, 90])

        # Check that the annotation and satellite plot setup loop works correctly
        for satIdx in range(max_sats):
            self.assertEqual(len(plot.sats_plot[satIdx]), 1)
            self.assertEqual(plot.sats_plot[satIdx][0]._color, 'g')

        # Ensure ion is called to enable interactive mode
        mock_ion.assert_called_once()

    @patch('matplotlib.pyplot.draw')
    @patch('matplotlib.pyplot.pause')
    @patch('matplotlib.pyplot.show')
    def test_update_plot(self, mock_show, mock_pause, mock_draw):
        # Prepare
        max_sats = 3
        plot = SkyPlot(max_sats)
        default_coords = (-5, -5)

        # Mock data for ephemeris and azelev
        ephemeris = [
            MagicMock(signalHealth=False),
            MagicMock(signalHealth=True),
            MagicMock(signalHealth=False)
        ]
        azelev = [
            [45, 20],  # Azimuth 45, Elevation 20
            [90, 15],  # Azimuth 90, Elevation 15
            [180, -10]  # Azimuth 180, Elevation -10 (should not be plotted)
        ]

        # Execute
        plot.update_plot(ephemeris, azelev)

        # Verify
        mock_show.assert_called_once()
        mock_draw.assert_called_once()
        mock_pause.assert_called_once()

        # Check if the alpha values are set correctly
        self.assertEqual(plot.sats_plot[0][0]._alpha, 1)  # Visible satellite
        self.assertEqual(plot.sats_plot[1][0]._alpha, 1)  # Visible satellite
        self.assertEqual(plot.sats_plot[2][0]._alpha, 0)  # Invisible satellite (below horizon)

        # Check that the color of the satellite is set correctly based on signalHealth
        self.assertEqual(plot.sats_plot[0][0]._color, 'g')  # Healthy satellite
        self.assertEqual(plot.sats_plot[1][0]._color, 'r')  # Unhealthy satellite
        self.assertEqual(plot.sats_plot[2][0]._color, 'g')  # Healthy satellite

        # Check that the annotation is updated with the correct coordinates
        self.assertEqual(plot.annot[0].xy, [azelev[0][0] / 180 * pi, azelev[0][1]])
        self.assertEqual(plot.annot[1].xy, [azelev[1][0] / 180 * pi, azelev[1][1]])
        self.assertEqual(plot.annot[2].xy, (default_coords[0], default_coords[1]))

if __name__ == '__main__':
    unittest.main()