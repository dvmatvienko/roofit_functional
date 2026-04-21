"""Module to compose a data container."""
from typing import Any, Tuple
from trycast import isassignable
import numpy as np
import pandas as pd

try:
    import ROOT
except ImportError as e:
    raise ImportError(
        "ROOT is not properly installed. Plase install ROOT support first"
    ) from e

from roofit_functional.RooFitFunction import RooFitFunction


# ========== Module to compose dataset for fitter  ==========
class RooFitData:
    """It converts various tabular data formats to the internal data container or generates a dataset.

    **Examples**

        pdf: RooFitFunction object describing 2-dimensional PDF

    >>> binned_generated_data = RooFitData("2D-binned-data","binned",(pdf,300000),pdf.x,bins=[50,50],seed=1234)

    >>> source = np.random.default_rng(1234).multivariate_normal([0,1],np.identity(2),(1000,)).T
    >>> unbinned_numpy_data = RooFitData("2D-unbinned-data","unbinned",source,pdf.x)
    """

    def __init__(
        self,
        name: str,
        datatype: str,
        source: Any,
        variables: list,
        bins: list[int] | None = None,
        cut: str = "",
        seed: int = 0,
    ) -> None:
        """Initialize RTooFitData object.

        Args:
            name: string defining dataset name
            datatype: string defining binned / unbinned dataset
            source: external data container or tuple giving data generation conditions
            variables: python list defining rhe PDF variables
            bins: (optional) python list defining the binning scheme for binned data
            cut: (optional) string defingn a cut region in the data space
            seed: (optional) int to fix random generator seed

        """
        self._name = name
        self._datatype = datatype
        self._source = source
        self._variables = variables

        # ROOT.ROOT.RDataFrame instead of ROOT.RDataFrame in ROOT version 6.36.02 (bug??)
        RDataFrameType = (
            ROOT.ROOT.RDataFrame
            if isinstance(ROOT.ROOT.RDataFrame, type)
            else ROOT.RDataFrame
        )

        if datatype == "unbinned":
            # Unbinned RooDataSet can be filled from TTree, ASCII file, numpy/pandas, RDataFrame, or (generate from RooFitFunction object)
            if isassignable(source, Tuple[RooFitFunction, int]):
                ROOT.RooRandom.randomGenerator().SetSeed(seed)
                ROOT.gRandom.SetSeed(seed)
                self._dataset = source[0].function.generate(set(variables), source[1])
            # ROOT.ROOT.RDataFrame instead of ROOT.RDataFrame in root version 6.36.02 (bug??)
            elif not isinstance(
                source,
                (
                    ROOT.TTree,
                    str,
                    ROOT.RooDataSet,
                    np.ndarray,
                    pd.DataFrame,
                    RDataFrameType,
                ),
            ):
                raise TypeError(
                    "wrong source is chosen for unbinned DataSet. It must be one of follows: ROOT.TTree, name of ASCII file, numpy array, pandas dataframe or RDataFrame"
                )
            if isinstance(source, ROOT.TTree):
                self._dataset = ROOT.RooDataSet(
                    name, name, set(variables), Import=source, Cut=cut
                )
            elif isinstance(source, str):
                self._dataset = ROOT.RootDataSet.read(source, variables)
            elif isinstance(source, ROOT.RooDataSet):
                self._dataset = source
            elif isinstance(source, np.ndarray):
                if len(source.shape) == 1:
                    source = source.reshape(1, -1)
                elif len(source.shape) > 2:
                    raise ValueError(
                        "please provide numpy array of 1-d or 2d. Numpy raws numerates variables but columns are events"
                    )
                if not source.shape[0] == len(variables):
                    raise ValueError(
                        "'variables' list must have length equal to numpy array raws"
                    )
                ll = [(k.GetName(), v) for k, v in zip(variables, source)]
                self._dataset = ROOT.RooDataSet.from_numpy(dict(ll), variables)
            elif isinstance(source, pd.DataFrame):
                if not len(source.columns) == len(variables):
                    raise ValueError(
                        "'variables' list must have length equal to number of pandas DataFrame columns"
                    )
                ll = [
                    (k.GetName(), source[v]) for k, v in zip(variables, source.columns)
                ]
                self._dataset = ROOT.RooDataSet.from_pandas(dict(ll), variables)
            elif isinstance(source, RDataFrameType):
                if not len(source.GetColumnNames()) == len(variables):
                    raise ValueError(
                        "'variables' list must have length equal to number of  RDataFrame columns"
                    )
                self._dataset = source.Book(
                    ROOT.std.move(
                        ROOT.RooDataSetHelper(name, name, ROOT.RooArgSet(*variables))
                    ),
                    source.GetColumnNames(),
                ).GetValue()
            self._bins = bins

        elif datatype == "binned":
            # Binned RooDataSet can be filled from THxx or unbinned dataset ,numpy/pandas, RDataFrame or (generate from RooFitFunction object)
            if isassignable(source, Tuple[RooFitFunction, int]):
                for i in range(len(variables)):
                    variables[i].setBins(bins[i])
                ROOT.RooRandom.randomGenerator().SetSeed(seed)
                ROOT.gRandom.SetSeed(seed)
                self._dataset = source[0].function.generateBinned(
                    set(variables), source[1]
                )
            elif not isinstance(
                source,
                (
                    ROOT.TH1,
                    ROOT.TH2,
                    ROOT.TH3,
                    type(self),
                    ROOT.RooDataSet,
                    np.ndarray,
                    pd.DataFrame,
                    RDataFrameType,
                ),
            ):
                raise TypeError(
                    "wrong source is chosen for binned DataSet. It must be one of follows: ROOT.THx, unbinned Dataset, numpy array or RDaTaFrame"
                )
            if not isinstance(bins, (int, list, np.ndarray)):
                raise ValueError(
                    "keyword parameter 'bins' could be int or list of ints (equal binning) or list of np.ndarray (bin edges)"
                )
            if isinstance(source, (ROOT.TH1, ROOT.TH2, ROOT.TH3)):
                self._dataset = ROOT.RooDataHist(name, name, variables, Import=source)
            elif isinstance(source, (type(self), ROOT.RooDataSet)):
                for i in range(len(variables)):
                    variables[i].setBins(bins[i])
                if isinstance(source, type(self)):
                    self._dataset = source.dataset.binnedClone()
                else:
                    self._dataset = source.binnedClone()
                for i in range(len(variables)):
                    variables[i].setBins(100)
            elif isinstance(source, np.ndarray):
                if isinstance(bins, int):
                    bins = [bins]
                if not source.shape[1] == len(variables):
                    raise ValueError(
                        "'variables' list must have length equal to numpy array columns"
                    )
                if all([type(v) is int for v in bins]):
                    # equal binning over dimensions
                    ranges = [tuple(v.getRange()) for v in variables]
                    counts, _ = np.histogramdd(source, bins=bins, range=ranges)
                    self._dataset = ROOT.RooDataHist.from_numpy(
                        counts.reshape(-1, 1), variables, bins=bins, ranges=ranges
                    )
                else:
                    # non-equal binning over at least one dimension  (bin edges)
                    counts, _ = np.histogramdd(source, bins=bins)
                    self._dataset = ROOT.RooDataHist.from_numpy(counts, variables, bins)
            elif isinstance(source, pd.DataFrame):
                raise TypeError(
                    "pandas dataframe has not been implemented yet for binned RooFitData!! Please convert pandas to numpy and provide numpy array"
                )
            elif isinstance(source, RDataFrameType):
                if not len(source.GetColumnNames()) == len(variables):
                    raise ValueError(
                        "'variables' list must have length equal to number of  RDataFrame columns"
                    )
                if isinstance(bins, int):
                    bins = np.array([bins])
                elif isinstance(bins, list):
                    bins = np.array(bins)
                if len(bins.shape) > 1:
                    bins = bins.reshape(-1)
                if not len(bins) == len(variables):
                    raise ValueError(
                        "'variables' list must have length equal to 'bins' list"
                    )
                for b, v in zip(bins, variables):
                    v.setBins(b)
                self._dataset = source.Book(
                    ROOT.std.move(
                        ROOT.RooDataHistHelper(name, name, ROOT.RooArgSet(*variables))
                    ),
                    source.GetColumnNames(),
                ).GetValue()
            self._bins = bins if isinstance(bins, (list, np.ndarray)) else [bins]

    @property
    def dataset(self):
        """Getter foir datatset."""
        return self._dataset

    @property
    def datatype(self):
        """Getter for datatype."""
        return self._datatype

    @property
    def bins(self):
        """Getter for bins."""
        return self._bins

    @property
    def name(self):
        """Getter for name."""
        return self._name
