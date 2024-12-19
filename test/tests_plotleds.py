import unittest
from unittest.mock import MagicMock, patch

from gnss_monitor.plotleds import *


class TestLedPlot(unittest.TestCase):

    def setUp(self):
        # Mock the strip object
        self.mock_strip = MagicMock()
        self.mock_strip.numPixels.return_value = 100  # Example: 100 LEDs
        self.mock_strip.getBrightness.return_value = 255

        # Mock the getPixelColorRGB method by mocking an RGB class
        class MockRGB:
            def __init__(self, r, g, b):
                self.r = r
                self.g = g
                self.b = b

        # Mock the getPixelColorRGB function to return red and blue alternating
        self.mock_strip.getPixelColorRGB.side_effect = \
            lambda idx: MockRGB(255, 0, 0) if idx % 2 == 0 else MockRGB(0, 0, 255)

        self.led_plot = LedPlot(width=10, strip=self.mock_strip)

    @patch("matplotlib.pyplot.plot")
    @patch("matplotlib.pyplot.subplots")
    def test_initialization(self, mock_subplots, mock_plot):
        # Prepare
        # Mock subplots and plot to avoid real plotting
        mock_ax = MagicMock()
        mock_fig = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        # Execute
        led_plot = LedPlot(width=10, strip=self.mock_strip)

        # Verify
        # Check dimensions
        self.assertEqual(led_plot.width, 10)
        self.assertEqual(led_plot.numleds, 100)
        self.assertEqual(led_plot.height, 10)

        # Check annotation and plot initialization
        self.assertEqual(len(led_plot.annot), 100)
        self.assertEqual(len(led_plot.leds_plot), 100)
        mock_plot.assert_called()

    @patch("matplotlib.lines.Line2D.set_color")
    def test_update_plot(self, mock_set_color):
        # Execute
        self.led_plot.update_plot()

        # Verify
        # Check that the plot updates for each LED
        self.assertEqual(mock_set_color.call_count, self.mock_strip.numPixels())

        # Ensure colors are set correctly for even and odd LEDs
        expected_calls = [
                             [1, 0, 0, 1],  # Bright red
                             [0, 0, 1, 1]  # Bright blue
                         ] * (self.mock_strip.numPixels() // 2)
        actual_calls = [call[0] for call in mock_set_color.call_args_list]
        rgb_alpha_values = [call[1] for call in actual_calls]
        self.assertListEqual(rgb_alpha_values, expected_calls)

        # Verify the plot title
        updated_title = self.led_plot.ax.get_title()
        self.assertIn('Latest update', updated_title)


if __name__ == "__main__":
    unittest.main()
