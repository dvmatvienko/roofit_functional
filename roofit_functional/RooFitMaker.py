"""Module to fit to data with RooFitFunction object."""
import sys
from pathlib import Path

try:
    import ROOT
except ImportError as e:
    raise ImportError(
        "ROOT is not properly installed. Plase install ROOT support first"
    ) from e

from roofit_functional.RooFitFunction import RooFitFunction
from roofit_functional.RooFitData import RooFitData


# ========== Module to make fit to data with PDF from RooFitFunction object  ==========
class RooFitMaker:
    """It makes fit to dataset from RooFitData object with PDF from RooFitFunction object.

     **Examples**
         pdf:RooFitFunction object describing PDF

    >>>r = RooFitMaker(binned_data,pdf,"ML")
    >>>r.dump_to_file() #Dump fit results to text file
    """

    def __init__(
        self,
        data: RooFitData,
        pdf: RooFitFunction,
        fittype: str,
        Range: dict[str, tuple[int | float]] | str = "",
        ExternalConstraints: set = set(),
        Minos: set | bool = False,
        Hesse: bool = True,
        **kwargs
    ) -> None:
        """Initialize RooFitMaker object.

        Args:
            data: RooFitData object
            pdf: RooFitFunction object
            fittype: string ('ML' / 'chi2') defining a fit to data method
            Range: (optional )python dict initializing fir range for PDF variable / string name defining prior prepared variable range
            ExternalConstraints: (optional) python set defining external constraints to likelihood by multiplying them with the original likelihood
            Minos: (optional): Flag controls if MINOS is run after HESSE / python set running MINOS on given subset of arguments
            Hesse: (optional): Flag controls if HESSE is run after MIGRAD

        """
        #'fittype' could be ML (binned / unbinned) or chi2 (binned)
        #'Range' is Dict[str,Tuple] w/ key : x.GetName() and value :(x_low,x_high)
        # Only one range is implemented. Joint ranges are not supported here yet!
        if not isinstance(Range, (str, dict)):
            raise TypeError(
                "wrong type of parameter 'Range'. It must be dict[str,tuple[int|float]] / str"
            )
        if isinstance(Range, dict):
            for k, v in Range.items():
                if v[0] >= v[1]:
                    raise ValueError(f"range of variable {k} is not correct!")
                for x in pdf.x:
                    if x.GetName() == k:
                        x.setRange("Range", *v)
            Range = "Range"

        if fittype == "ML":
            # construct ML of pdf w.r.t data
            self._cost = pdf.function.createNLL(
                data.dataset,
                Extended=pdf.get_extended(),
                GlobalObservables=pdf.x,
                Range=Range,
                ExternalConstraints=ExternalConstraints,
            )
            # create RooFitResult object
            self._r = pdf.function.fitTo(
                data.dataset,
                Extended=pdf.get_extended(),
                GlobalObservables=pdf.x,
                Range=Range,
                Save=True,
                PrintLevel=-1,
                ExternalConstraints=ExternalConstraints,
                Minos=Minos,
                Hesse=Hesse,
                **kwargs
            )
        elif fittype == "chi2":
            if data.datatype == 'unbinned':
                raise ValueError(f"chi2 fit is valid only for unbinned data, but datatype used is {data.datatype}")
            self._cost = pdf.function.createChi2(
                data.dataset,
                Extended=pdf.get_extended(),
                GlobalObservables=pdf.x,
                Range=Range,
                ExternalConstraints=ExternalConstraints,
            )
            self._r = pdf.function.chi2FitTo(
                data.dataset,
                Extended=pdf.get_extended(),
                GlobalObservables=pdf.x,
                Range=Range,
                Save=True,
                PrintLevel=-1,
                ExternalConstraints=ExternalConstraints,
                Minos=Minos,
                Hesse=Hesse,
                **kwargs
            )

        # pdf.set_NFitFloated(len(list(self._r.floatParsFinal())))
        self._pdf = pdf

    def dump_to_file(self, ofile: str = "fitresult.txt") -> None:
        """Dump fit results to file.

        Args:
            ofile: (optional) string defining the filenam

        """
        ofile = Path(ofile)
        r = self._r
        cov = r.covarianceMatrix()
        cor = r.correlationMatrix()

        # Create temp file to fill in RooFitResult multilines
        f = ROOT.std.ofstream("temp")
        # self._cost.Print("v")
        r.printMultiline(f, 1111, True)
        r.printValue(f)
        f.close()
        temp = Path("temp")

        # Create temp2 file to fill in separate values  from the fit
        orig = sys.stdout
        temp2 = Path("temp2")
        with temp2.open("w") as fi:
            sys.stdout = fi
            try:
                print("\n")
                print("Status : ", r.status())
                print("Error matrix quality : ", r.covQual())
                print("FCN : ", r.minNll())
                print("EDM :", r.edm())
                print(
                    "List of fixed parameters :", *[v for v in r.constPars()], sep="\n"
                )
                print(
                    "List of floating parameters (Minos error, if ON)):",
                    *[v for v in r.floatParsFinal()],
                    sep="\n",
                )
                print(
                    "Covariance Matrix : ",
                    *[
                        [cov(raw, col) for col in range(cov.GetNcols())]
                        for raw in range(cov.GetNrows())
                    ],
                    sep="\n",
                )
                print(
                    "Correlation Matrix : ",
                    *[
                        [cor(raw, col) for col in range(cor.GetNcols())]
                        for raw in range(cor.GetNrows())
                    ],
                    sep="\n",
                )
                print(
                    "Hesse errors : ",
                    *[(x.GetName(), x.getError()) for x in r.floatParsFinal()],
                    sep="\n",
                )
            finally:
                sys.stdout = orig

        # Combine temp & temp2 to result 'ofile'
        with ofile.open("w") as ofi:
            for ifile in [temp, temp2]:
                with ifile.open("r") as ifi:
                    for line in ifi:
                        ofi.write(line)

        # Remove temp & temp2
        for ifile in [temp, temp2]:
            ifile.unlink()

    def give_fit_results(self, Minos: bool = False) -> dict:
        """Give fit results as a python dict.

        Args:
            Minos: (optional) Flag controls if MINOS is run after HESSE

        """
        r = self._r
        # results = list(r.floatParsFinal()) + list(r.constPars())
        results = list(r.floatParsFinal())
        if not Minos:
            return {x.GetName(): [x.getValV(), x.getError()] for x in results}
        else:
            return {
                x.GetName(): [x.getValV(), (x.getErrorLo(), x.getErrorHi())]
                for x in results
            }

    def give_fit_quality(self) -> dict:
        """Give fit quality status as python dict."""
        r = self._r
        return {"Status": r.status(), "Quality": r.covQual(), "EDM": r.edm()}


# ========== Simple examples for the module ==========
if __name__ == "__main__":
    # Delta E 1-dim RooFit function test
    de_cb = RooFitFunction(
        "CrystalBall1",
        {"dE": [-0.15, 0.15]},
        "CrystalBall",
        {
            "x0CB": [0, -0.01, 0.01],
            "sigmacbL": [0.02, 0.005, 0.05],
            "sigmacbR": [0.02, 0.005, 0.05],
            "alphaL": [0.1, 0.005, 2],
            "alphaR": [0.1, 0.005, 2],
            "nL": [1, 0.1, 20.0],
            "nR": [1, 0.1, 20.0],
        },
    )

    de_bfGauss = RooFitFunction(
        "Gauss",
        {"all": de_cb},
        "BifurGauss",
        {
            "x0": [0, -0.01, 0.01],
            "sigmaL": [0.01, 0.001, 0.05],
            "sigmaR": [0.01, 0.001, 0.05],
        },
    )

    de_pdf = de_cb.get_add(de_bfGauss, {"frac": [0.5, 0.0, 1.0]})

    # Omega 1-dim RooFit function test
    mom_bw = RooFitFunction(
        "BreitWigner",
        {"mom": [0.74, 0.855]},
        "BreitWigner",
        {"mean": [0.78265, 0, 0], "width": [0.0085, 0, 0]},
    )

    mom_cb = RooFitFunction(
        "CrystalBall2",
        {"all": mom_bw},
        "CrystalBall",
        {
            "mom_x0CB": [0, 0, 0],
            "mom_sigcbL": [0.005, 0.001, 0.05],
            "mom_sigcbR": [0.005, 0.001, 0.05],
            "mom_alphaL": [1, 0.005, 2],
            "mom_alphaR": [1, 0.005, 2],
            "mom_nL": [1, 0.01, 50.0],
            "mom_nR": [1, 0.01, 50.0],
        },
    )

    mom_pdf = mom_bw.get_convolution(mom_cb)

    # (Delta E - Omega) RooFit uncorr. product
    de_mom_uncorr = mom_pdf * de_pdf

    #    data = de_mom_uncorr.function.generate(set(de_mom_uncorr.x),500000)
    binned_data = RooFitData(
        "test", "binned", (de_mom_uncorr, 500000), de_mom_uncorr.x, bins=[100, 100]
    )
    r = RooFitMaker(binned_data, de_mom_uncorr, "ML")
    r.dump_to_file()
