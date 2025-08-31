import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from roofit_functional.RooFitMaker import RooFitMaker

class TestRooFitMaker(unittest.TestCase):
    def setUp(self):
        # Mock RooFitFunction and RooFitData
        self.mock_pdf = MagicMock()
        self.mock_pdf.x = [MagicMock(GetName=MagicMock(return_value="x"))]
        self.mock_pdf.function.createNLL.return_value = MagicMock()
        self.mock_pdf.function.fitTo.return_value = MagicMock()
        self.mock_pdf.function.createChi2.return_value = MagicMock()
        self.mock_pdf.function.chi2FitTo.return_value = MagicMock()
        self.mock_pdf.get_extended.return_value = False

        self.mock_data = MagicMock()
        self.mock_data.dataset = MagicMock()

        # Mock RooFitResult
        self.mock_result = MagicMock()
        self.mock_result.covarianceMatrix.return_value = MagicMock(GetNcols=MagicMock(return_value=1), GetNrows=MagicMock(return_value=1), __call__=lambda r, c: 1.0)
        self.mock_result.correlationMatrix.return_value = MagicMock(GetNcols=MagicMock(return_value=1), GetNrows=MagicMock(return_value=1), __call__=lambda r, c: 0.5)
        self.mock_result.floatParsFinal.return_value = [MagicMock(GetName=MagicMock(return_value="par1"), getValV=MagicMock(return_value=1.0), getError=MagicMock(return_value=0.1), getErrorLo=MagicMock(return_value=-0.1), getErrorHi=MagicMock(return_value=0.2))]
        self.mock_result.constPars.return_value = [MagicMock(GetName=MagicMock(return_value="const1"))]
        self.mock_result.status.return_value = 0
        self.mock_result.covQual.return_value = 3
        self.mock_result.edm.return_value = 0.001
        self.mock_result.minNll.return_value = 123.45

        self.mock_pdf.function.fitTo.return_value = self.mock_result
        self.mock_pdf.function.chi2FitTo.return_value = self.mock_result

    def test_init_with_valid_range_dict(self):
        range_dict = {"x": (0, 1)}
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "ML", Range=range_dict)
        self.assertIsInstance(maker, RooFitMaker)

    def test_init_with_valid_range_str(self):
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "ML", Range="Range")
        self.assertIsInstance(maker, RooFitMaker)

    def test_init_with_invalid_range_type(self):
        with self.assertRaises(TypeError):
            RooFitMaker(self.mock_data, self.mock_pdf, "ML", Range=123)

    def test_init_with_invalid_range_values(self):
        range_dict = {"x": (1, 0)}
        with self.assertRaises(ValueError):
            RooFitMaker(self.mock_data, self.mock_pdf, "ML", Range=range_dict)

    def test_init_with_chi2_fittype(self):
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "chi2")
        self.assertIsInstance(maker, RooFitMaker)

    @patch("roofit_functional.RooFitMaker.ROOT")
    def test_dump_to_file_creates_and_removes_files(self, mock_root):
        # Patch ROOT.std.ofstream and Path.unlink
        mock_ofstream = MagicMock()
        mock_root.std.ofstream.return_value = mock_ofstream
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "ML")
        with patch.object(Path, "open", MagicMock()), \
             patch.object(Path, "unlink", MagicMock()):
            maker.dump_to_file("test_fitresult.txt")
        mock_ofstream.close.assert_called_once()

    def test_give_fit_results_without_minos(self):
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "ML")
        result = maker.give_fit_results(Minos=False)
        self.assertIn("par1", result)
        self.assertEqual(result["par1"], [1.0, 0.1])

    def test_give_fit_results_with_minos(self):
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "ML")
        result = maker.give_fit_results(Minos=True)
        self.assertIn("par1", result)
        self.assertEqual(result["par1"], [1.0, (-0.1, 0.2)])

    def test_give_fit_quality(self):
        maker = RooFitMaker(self.mock_data, self.mock_pdf, "ML")
        quality = maker.give_fit_quality()
        self.assertEqual(quality["Status"], 0)
        self.assertEqual(quality["Quality"], 3)
        self.assertEqual(quality["EDM"], 0.001)

if __name__ == "__main__":
    unittest.main()
