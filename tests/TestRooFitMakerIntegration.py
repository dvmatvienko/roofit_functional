"""
Integration tests for the RooFitMaker class should verify its 
interaction with RooFitFunction and RooFitData, 
and check that fitting, result dumping, and result extraction work as expected
"""
import pytest
#from pathlib import Path
import numpy as np
from roofit_functional.RooFitMaker import RooFitMaker
from roofit_functional.RooFitFunction import RooFitFunction
from roofit_functional.RooFitData import RooFitData

@pytest.fixture
def gauss_pdf():
    return RooFitFunction(
        "Gauss",
        {"x": [-1, 1]},
        "Gaussian",
        {"mean": [0, -1, 1], "sigma": [1, 0.1, 2]}
    )

@pytest.fixture
def data(gauss_pdf):
    datatype = str(np.random.choice(["binned","unbinned"]))
    bins = [50] if datatype == 'binned' else None
    return RooFitData(
        "test", datatype, (gauss_pdf, 1000), gauss_pdf.x, bins=bins
    )

@pytest.mark.parametrize("par",["mean","sigma"])
def test_ml_fit_results(data, gauss_pdf, par):
    maker = RooFitMaker(data, gauss_pdf, "ML")
    results = maker.give_fit_results()
    assert par in results
    assert isinstance(results[par][0], float)

@pytest.mark.parametrize("par",["mean","sigma"])
def test_chi2_fit_results(data, gauss_pdf, par):
    if data.datatype == 'unbinned':
        with pytest.raises(ValueError):
            RooFitMaker(data, gauss_pdf, "chi2")
    else:
        maker = RooFitMaker(data, gauss_pdf, "chi2")
        results = maker.give_fit_results()
        assert par in results

@pytest.mark.parametrize("par",["Status","Quality","EDM"])
def test_fit_quality(data, gauss_pdf, par):
    maker = RooFitMaker(data, gauss_pdf, "ML")
    quality = maker.give_fit_quality()
    assert par in quality

@pytest.mark.parametrize("par",["Status","Covariance Matrix"])
def test_dump_to_file(tmp_path, data, gauss_pdf, par):
    maker = RooFitMaker(data, gauss_pdf, "ML")
    out_file = tmp_path / "fitresult.txt"
    maker.dump_to_file(str(out_file))
    assert out_file.exists()
    content = out_file.read_text()
    assert par in content

def test_range_dict_valid(data, gauss_pdf):
    range_dict = {"x": [-0.5, 0.5]}
    maker = RooFitMaker(data, gauss_pdf, "ML", Range=range_dict)
    results = maker.give_fit_results()
    assert "mean" in results

def test_range_dict_invalid(data, gauss_pdf):
    range_dict = {"x": [1, -1]}  # invalid: low >= high
    with pytest.raises(ValueError):
        RooFitMaker(data, gauss_pdf, "ML", Range=range_dict)

def test_external_constraints(data, gauss_pdf):
    constraints = set()
    maker = RooFitMaker(data, gauss_pdf, "ML", ExternalConstraints=constraints)
    results = maker.give_fit_results()
    assert "mean" in results

def test_minos_flag(data, gauss_pdf):
    maker = RooFitMaker(data, gauss_pdf, "ML", Minos=True)
    results = maker.give_fit_results(Minos=True)
    assert isinstance(results["mean"][1], tuple)

def test_hesse_flag(data, gauss_pdf):
    maker = RooFitMaker(data, gauss_pdf, "ML", Hesse=False)
    results = maker.give_fit_results()
    assert "mean" in results

def test_invalid_range_type(data, gauss_pdf):
    with pytest.raises(TypeError):
        RooFitMaker(data, gauss_pdf, "ML", Range=123)
