import ROOT 
from typing import Any, List
import numpy as np
import pandas as pd
from math import prod

class RooFitData:
    # datatype: unbinned / binned 
    def __init__(self, name : str, datatype : str, source, variables : List, bins = None, cut :  str = ""):
        self._name = name
        self._datatype = datatype
        self._source = source
        self._variables = variables

        if datatype == 'unbinned':
            # Unbinned RooDataSet can be filled from TTree, ASCII file, numpy/pandas, RDataFrame
            if not isinstance(source,(ROOT.TTree,str,ROOT.RooDataSet,np.ndarray,pd.DataFrame,ROOT.RDataFrame)):
                raise TypeError("wrong source is chosen for unbinned DataSet. It must be one of follows: ROOT.TTree, name of ASCII file, numpy array, pandas dataframe or RDataFrame")
            if isinstance(source,ROOT.TTree):
                self._dataset = ROOT.RooDataSet(name,name,set(variables),Import=source, Cut=cut)
            elif isinstance(source,str):
                self._dataset = ROOT.RootDataSet.read(source,variables)
            elif isinstance(source,ROOT.RooDataSet):
                self._dataset = source
            elif isinstance(source,np.ndarray):
                if len(source.shape) == 1:
                    source = source.reshape(1,-1)
                elif len(source.shape) > 2:
                    raise ValueError("please provide numpy array of 1-d or 2d. Numpy raws numerates variables but columns are events")
                if not source.shape[0] == len(variables):
                    raise ValueError("'variables' list must have length equal to numpy array raws")
                ll = [(k.GetName(),v) for k,v in zip(variables,source)]
                self._dataset = ROOT.RooDataSet.from_numpy(dict(ll),variables)
            elif isinstance(source,pd.DataFrame):
                if not len(source.columns) == len(variables):
                    raise ValueError("'variables' list must have length equal to number of pandas DataFrame columns")
                ll = [(k.GetName(),source[v]) for k,v in zip(variables,source.columns)]
                self._dataset = ROOT.RooDataSet.from_pandas(dict(ll),variables)
            elif isinstance(source,ROOT.RDataFrame):
                if not len(source.GetColumnNames()) == len(variables):
                    raise ValueError("'variables' list must have length equal to number of  RDataFrame columns")
                self._dataset = source.Book(ROOT.std.move(ROOT.RooDataSetHelper(name,name,ROOT.RooArgSet(*variables))),source.GetColumnNames()).GetValue()
            self._bins = bins

        elif datatype == 'binned':
            # Binned RooDataSet can be filled from THxx or unbinned dataset ,numpy/pandas, RDataFrame
            if not isinstance(source,(ROOT.TH1,ROOT.TH2,ROOT.TH3,type(self),ROOT.RooDataSet,np.ndarray,pd.DataFrame,ROOT.RDataFrame)):
               raise TypeError("wrong source is chosen for binned DataSet. It must be ROOT.THx, unbinned Dataset, numpy array or RDaTaFrame")
            if not isinstance(bins,(int,list,np.ndarray)):
               raise ValueError("keyword parameter 'bins' could be int or list of ints (equal binning) or list of np.ndarray (bin edges)")
            if isinstance(source,(ROOT.TH1,ROOT.TH2,ROOT.TH3)):
                self._dataset = ROOT.RooDataHist(name,name,variables,Import=source)
            elif isinstance(source,(type(self),ROOT.RooDataSet)):
                if isinstance(source,type(self)):
                    self._dataset = source.get_dataset().binnedClone()
                else:
                    self._dataset = source.binnedClone()
            elif isinstance(source,np.ndarray):
                if isinstance(bins,int):
                    bins = [bins]
                if not source.shape[1] == len(variables):
                    raise ValueError("'variables' list must have length equal to numpy array columns")
                if all([type(v) == int for v in bins]):
                    #equal binning over dimensions
                    ranges = [tuple(v.getRange()) for v in variables]
                    counts, _ = np.histogramdd(source,bins=bins,range=ranges)
                    self._dataset = ROOT.RooDataHist.from_numpy(counts.reshape(-1,1),variables,bins=bins,ranges=ranges)
                else:
                    # non-equal binning over at least one dimenson  (bin edges)
                    counts, _ = np.histogramdd(source, bins=bins)
                    self._dataset = ROOT.RooDataHist.from_numpy(counts,variables,bins)
            elif isinstance(source,pd.DataFrame):
                raise TypeError("pandas dataframe has not been implemented yet for binned RooFitData!! Please convert pandas to numpy and provide numpy array")
            elif isinstance(source,ROOT.RDataFrame):
                if not len(source.GetColumnNames()) == len(variables):
                    raise ValueError("'variables' list must have length equal to number of  RDataFrame columns")
                if isinstance(bins,int):
                    bins = np.array([bins])
                elif isinstance(bins,list):
                    bins = np.array(bins)
                if len(bins.shape) > 1:
                    bins = bins.reshape(-1)
                if not len(bins) == len(variables):
                    raise ValueError("'variables' list must have length equal to 'bins' list")
                for b,v in zip(bins,variables):
                    v.setBins(b)
                self._dataset = source.Book(ROOT.std.move(ROOT.RooDataHistHelper(name,name,ROOT.RooArgSet(*variables))),source.GetColumnNames()).GetValue()
            self._bins = bins if isinstance(bins,(list,np.ndarray)) else [bins]

    def get_dataset(self):
        return self._dataset

    def get_datatype(self):
        return self._datatype

    def get_bins(self):
        return self._bins

    def get_name(self):
        return self._name


