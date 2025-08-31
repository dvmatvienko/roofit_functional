import unittest
from unittest.mock import MagicMock, patch

from roofit_functional.RooFitPlot import RooFitPlot

class TestRooFitPlot(unittest.TestCase):
    def setUp(self):
        # Mock ROOT and its classes
        self.mock_root = patch("roofit_functional.RooFitPlot.ROOT").start()
        self.addCleanup(patch.stopall)
        self.mock_frame = MagicMock()
        self.mock_root.RooPlot = self.mock_frame
        self.mock_canvas = MagicMock()
        self.mock_root.TCanvas.return_value = self.mock_canvas
        self.mock_root.TFile.return_value = MagicMock()
        self.mock_root.TLine.return_value = MagicMock()
        
        # Mock RooFitFunction and RooFitData
        self.mock_x = MagicMock()
        self.mock_x.GetName.return_value = "x"
        self.mock_x.getRange.return_value = (0, 1)
        self.mock_x.frame.return_value = self.mock_frame
        self.mock_x.SetTitle = MagicMock()
        self.mock_x.GetXaxis.return_value = MagicMock()
        self.mock_x.GetYaxis.return_value = MagicMock()
        self.mock_x.SetLineColor = MagicMock()
        self.mock_x.SetLineStyle = MagicMock()
        self.mock_x.SetLineWidth = MagicMock()
        self.mock_x.SetTitleOffset = MagicMock()
        self.mock_x.GetZaxis.return_value = MagicMock()
        
        self.mock_pdf = MagicMock()
        self.mock_pdf.x = [self.mock_x]
        self.mock_pdf.name = "pdf"
        self.mock_pdf.function = MagicMock()
        self.mock_pdf.function_type = "type"
        self.mock_pdf.functionality = []
        self.mock_pdf.x_limits = {"x": (0, 1)}
        
        self.mock_data = MagicMock()
        self.mock_data.name = "data"
        self.mock_data.dataset = MagicMock()
        
    def test_init_valid_projection(self):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        self.assertIsInstance(plot, RooFitPlot)
        self.assertEqual(plot._projection, "x")
        
    def test_init_invalid_projection(self):
        with self.assertRaises(ValueError):
            RooFitPlot(self.mock_data, self.mock_pdf, "y", "title")
            
    def test_init_invalid_slice_type(self):
        with self.assertRaises(TypeError):
            RooFitPlot(self.mock_data, self.mock_pdf, "x", "title", Slice={"x": 1})
            
    def test_init_invalid_pdf_options(self):
        with self.assertRaises(ValueError):
            RooFitPlot(self.mock_data, self.mock_pdf, "x", "title", pdf_options={"InvalidOption": 1})
            
    def test_init_invalid_data_options(self):
        with self.assertRaises(ValueError):
            RooFitPlot(self.mock_data, self.mock_pdf, "x", "title", data_options={"InvalidOption": 1})
            
    def test_init_too_many_data_options(self):
        options = {f"Opt{i}": i for i in range(9)}
        with self.assertRaises(TypeError):
            RooFitPlot(self.mock_data, self.mock_pdf, "x", "title", data_options=options)
            
    def test_frame_property(self):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        self.assertEqual(plot.frame, plot._frame)
        
    def test_set_paramOn(self):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot.set_paramOn()
        plot._pdf.function.paramOn.assert_called()
        
    def test_set_statOn(self):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot.set_statOn()
        plot._data.dataset.statOn.assert_called()
        
    @patch("roofit_functional.RooFitPlot.ROOT")
    def test_make_plot(self, mock_root):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot._frame = MagicMock()
        plot.make_plot(filename="testplot", pdf_format=True, log=True)
        mock_root.TCanvas.return_value.SaveAs.assert_called()
        
    @patch("roofit_functional.RooFitPlot.ROOT")
    def test_make_pullplot(self, mock_root):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot._frame = MagicMock()
        plot._frame.pullHist.return_value = MagicMock()
        plot._x = [self.mock_x]
        plot.make_pullplot(filename="pullplot", pdf_format=False, log=False)
        mock_root.TCanvas.return_value.SaveAs.assert_called()
        
    @patch("roofit_functional.RooFitPlot.ROOT")
    def test_make_2d_plot_valid(self, mock_root):
        self.mock_pdf.x = [self.mock_x, self.mock_x]
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot._x = [self.mock_x, self.mock_x]
        plot._pdf = self.mock_pdf
        self.mock_pdf.function.createHistogram.return_value = MagicMock()
        plot.make_2d_plot(name="2d", filename="2dplot", pdf_format=True)
        mock_root.TCanvas.return_value.SaveAs.assert_called()
        
    def test_make_2d_plot_invalid(self):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot._x = [self.mock_x]
        with self.assertRaises(AttributeError):
            plot.make_2d_plot()
            
    def test_get_chi2(self):
        plot = RooFitPlot(self.mock_data, self.mock_pdf, "x", "title")
        plot._frame = MagicMock()
        plot._pdf = MagicMock()
        plot._pdf.get_NFitFloated.return_value = 1
        plot._frame.chiSquare.return_value = 1.23
        chi2 = plot.get_chi2()
        self.assertEqual(chi2, 1.23)

if __name__ == "__main__":
    unittest.main()
