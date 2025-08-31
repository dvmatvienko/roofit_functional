import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd

from roofit_functional.RooFitData import RooFitData

class DummyTTreeType: pass
class DummyRooDataSetType: 
    def from_numpy(self,*args,**kwargs):
        return "numpy_dataset"
    def from_pandas(self,*args,**kwargs):
        return "pandas_dataset"
class DummyRooDataHistType:
    def from_numpy(self,*args,**kwargs):
        return "hist_dataset"
class DummyRDataFrameType: pass
class DummyTH1Type: pass
class DummyTH2Type: pass
class DummyTH3Type: pass

class MockROOT:
    def __init__(self):
        self._setup_mocks()

    def _setup_mocks(self):
        self.ROOT = self
        self.TTree = DummyTTreeType
        self.RooDataSet = DummyRooDataSetType
        self.RooDataHist = DummyRooDataHistType
        self.RDataFrame = DummyRDataFrameType
        self.TH1 = DummyTH1Type
        self.TH2 = DummyTH2Type
        self.TH3 = DummyTH3Type


        self.RooRandom = MagicMock()
        self.gRandom = MagicMock()
        self.gRandom.randomGenerator.return_value.SetSeed = MagicMock()
        self.gRandom.SetSeed = MagicMock()

class TestRooFitData(unittest.TestCase):

    def setUp(self):
        self.mock_root = MockROOT()
        self.patcher = patch('roofit_functional.RooFitData.ROOT', self.mock_root)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("roofit_functional.RooFitData.isassignable", return_value=True)
    def test_unbinned_generate_from_roofitfunction(self,mock_assignable):
        mock_func = MagicMock()
        mock_func.function.generate.return_value = "generated_dataset"
        variables = [MagicMock()]
        data = RooFitData("test", "unbinned", (mock_func, 10), variables, seed=42)
        self.assertEqual(data.dataset, "generated_dataset")
        self.assertEqual(data.datatype, "unbinned")
        self.assertEqual(data.name, "test")

    def test_unbinned_numpy_array(self):
        variables = [MagicMock(getName=MagicMock(return_value="x")), MagicMock(getName=MagicMock(return_value="y"))]
        arr = np.array([[1, 2], [3, 4]])
        data = RooFitData("test", "unbinned", arr, variables)
        self.assertEqual(data.dataset, "numpy_dataset")


    def test_unbinned_numpy_array_wrong_shape(self):
        variables = [MagicMock(getName=MagicMock(return_value="x"))]
        arr = np.array([[1, 2], [3, 4]])
        with self.assertRaises(ValueError):
            RooFitData("test", "unbinned", arr, variables)

    def test_unbinned_pandas_dataframe(self):
        variables = [MagicMock(getName=MagicMock(return_value="x")), MagicMock(getName=MagicMock(return_value="y"))]
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        data = RooFitData("test", "unbinned", df, variables)
        self.assertEqual(data.dataset, "pandas_dataset")

    @patch("roofit_functional.RooFitData.isassignable", return_value=True)
    def test_binned_generate_from_roofitfunction(self, mock_isassignable):
        mock_func = MagicMock()
        mock_func.function.generateBinned.return_value = "binned_dataset"
        variables = [MagicMock(setBins=MagicMock())]
        data = RooFitData("test", "binned", (mock_func, 10), variables, bins=[5], seed=42)
        self.assertEqual(data.dataset, "binned_dataset")
        self.assertEqual(data.bins, [5])

    def test_binned_numpy_array_equal_binning(self):
        variables = [MagicMock(getRange=MagicMock(return_value=(0, 1)))]
        arr = np.random.rand(10, 1)
        data = RooFitData("test", "binned", arr, variables, bins=5)
        self.assertEqual(data.dataset, "hist_dataset")

    def test_binned_numpy_array_nonequal_binning(self):
        variables = [MagicMock(getRange=MagicMock(return_value=(0, 1)))]
        arr = np.random.rand(10, 1)
        bins = [np.linspace(0, 1, 6)]
        data = RooFitData("test", "binned", arr, variables, bins=bins)
        self.assertEqual(data.dataset, "hist_dataset")

    def test_binned_invalid_bins_type(self):
        variables = [MagicMock()]
        arr = np.random.rand(10, 1)
        with self.assertRaises(ValueError):
            RooFitData("test", "binned", arr, variables, bins="invalid")

    def test_binned_pandas_dataframe_not_implemented(self):
        variables = [MagicMock()]
        df = pd.DataFrame({"x": [1, 2]})
        with self.assertRaises(TypeError):
            RooFitData("test", "binned", df, variables, bins=5)

    def test_binned_invalid_source_type(self):
        variables = [MagicMock()]
        with self.assertRaises(TypeError):
            RooFitData("test", "binned", 123, variables, bins=5)

if __name__ == "__main__":
    unittest.main()
