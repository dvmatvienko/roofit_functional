"""
Integration tests for the RooFitPlot class should verify its 
interaction with RooFitFunction, RooFitData and RooFitMaker, 
and check that all the chain of operations works as expected
"""

import pytest
import os

from roofit_functional.RooFitFunction import RooFitFunction
from roofit_functional.RooFitData import RooFitData
from roofit_functional.RooFitMaker import RooFitMaker
from roofit_functional.RooFitPlot import RooFitPlot

@pytest.fixture
def setup_pdf_and_data():
    # Create PDF functions
    x_cb = RooFitFunction(
        "CrystalBall",
        {"x": [-0.15, 0.15]},
        "CrystalBall",
        {
            "x0CB": 0,
            "sigmacb": [0.02, 0.01, 0.03],
            "alphaL": 0.1,
            "nL": 1,
            "alphaR": 0.1,
            "nR": 1,
        },
    )
    x_Gauss = RooFitFunction(
        "Gauss", {"x": x_cb}, "Gaussian", {"mean": 0, "sigma": [0.05, 0.03, 0.07]}
    )
    x_pdf = x_cb.get_add(x_Gauss, {"frac": [0.3, 0.1, 0.9]})

    y_bw = RooFitFunction(
        "BreitWigner",
        {"y": [0.74, 0.87]},
        "BreitWigner",
        {"BWmean": 0.783, "BWidth": 0.0085},
    )
    y_Gauss = RooFitFunction(
        "MGauss",
        {"all": y_bw},
        "Gaussian",
        {"ymean": 0, "ysigma": [0.007, 0.001, 0.015]},
    )
    y_pdf = y_bw.get_convolution(y_Gauss, "y_pdf")
    product = x_pdf * y_pdf

    # Generate toy data
    binned_data = RooFitData(
        "2D-binned-data",
        "binned",
        (product, 10000),
        product.x,
        bins=[10, 10],
        seed=42,
    )

    # Fit PDF to data
    RooFitMaker(binned_data, product, "ML")
    return binned_data, product

def test_roofitplot_make_plot(tmp_path, setup_pdf_and_data):
    binned_data, product = setup_pdf_and_data
    plot = RooFitPlot(
        binned_data,
        product,
        "x",
        "x-projection",
        Slice={"y": (0.76, 0.80)},
    )
    plot.set_paramOn()
    plot.set_statOn()
    filename = tmp_path / "test_plot"
    plot.make_plot(str(filename), pdf_format=False)
    assert os.path.exists(str(filename) + ".png")
    assert os.path.exists(str(filename) + ".root")

def test_roofitplot_make_pullplot(tmp_path, setup_pdf_and_data):
    binned_data, product = setup_pdf_and_data
    plot = RooFitPlot(
        binned_data,
        product,
        "x",
        "x-projection",
        Slice={"y": (0.76, 0.80)},
    )
    filename = tmp_path / "test_pull"
    plot.make_pullplot(str(filename), pdf_format=True)
    assert os.path.exists(str(filename) + ".pdf")

def test_roofitplot_make_2d_plot(tmp_path, setup_pdf_and_data):
    binned_data, product = setup_pdf_and_data
    plot = RooFitPlot(
        binned_data,
        product,
        "x",
        "2D plot",
    )
    filename = tmp_path / "test_2d"
    plot.make_2d_plot(name="2D PDF", filename=str(filename), pdf_format=True)
    assert os.path.exists(str(filename) + ".pdf")

def test_roofitplot_chi2(setup_pdf_and_data):
    binned_data, product = setup_pdf_and_data
    plot = RooFitPlot(
        binned_data,
        product,
        "x",
        "x-projection",
        Slice={"y": (0.76, 0.80)},
    )
    chi2 = plot.get_chi2()
    assert isinstance(chi2, float)
    assert chi2 >= 0
