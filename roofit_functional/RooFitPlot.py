"""Module to plot data and PDF."""
from typing import Any
import re

try:
    import ROOT
except ImportError as e:
    raise ImportError(
        "ROOT is not properly installed. Plase install ROOT support first"
    ) from e

from roofit_functional.RooFitFunction import RooFitFunction
from roofit_functional.RooFitData import RooFitData
from roofit_functional.RooFitMaker import RooFitMaker


# ========== Module to plot data and model fitted to data with PDF from RooFitFunction object  ==========
class RooFitPlot:
    """It makes a plot with data and PDF model fitted to data.

     **Examples**
         pdf:RooFitFunction object describing PDF

    >>>p = RooFitPlot(binned_data,pdf,"x","x-projection in y-slice",Slice={'y' : (0.76,0.80)})
    """

    @staticmethod
    def get_object_map(
        pdf: RooFitFunction,
        pdf_mother: RooFitFunction | None = None,
        d: dict[tuple[RooFitFunction, RooFitFunction, int], RooFitFunction]
        | None = None,
        level: int = 0,
    ) -> dict[tuple[RooFitFunction, RooFitFunction, int], RooFitFunction]:
        """Create a chain with PDFs from a complex PDF.

        Args:
            pdf: RooFitFunction object with current PDF
            pdf_mother: (optional) RooFitFunction object referenced to mother of the current pdf
            d: (optional) python dict with current history of PDF chain
            level: (optional) int which is auxiliary indicator distinguishing PDFs with one PDF mother and name

        """
        if pdf_mother is None and d is None:
            d = {}
            pdf_mother = pdf
        d[(pdf.function_type, pdf_mother.function_type, level)] = pdf
        functionality = pdf.functionality
        if isinstance(functionality, list):
            for i in range(len(functionality)):
                if isinstance(functionality[i], type(pdf)):
                    RooFitPlot.get_object_map(
                        pdf.functionality[i], pdf_mother=pdf, d=d, level=i
                    )
                elif isinstance(functionality[i], dict):
                    RooFitPlot.get_object_map(
                        list(pdf.functionality[i].keys())[0],
                        pdf_mother=pdf,
                        d=d,
                        level=i,
                    )
        return d

    def __init__(
        self,
        data: RooFitData,
        pdf: RooFitFunction,
        projection: str,
        title: str | tuple[str],
        data_options: dict[str, Any] | None = None,
        pdf_options: dict[str, Any] | None = None,
        Range: tuple[int | float] = tuple(),
        Slice: dict[str, tuple[int | float]] | None = None,
        Bins: int | None = None,
        isHistogram: bool = False,
    ) -> None:
        """Initialize RooFitPlot object.

        Args:
            data: RooFitData object
            pdf: RooFitFunction object
            projection: string defining projection variable for the plot
            title: string or tuple of strings defining global title and axes titles (if tuple)
            data_options: (optional) python dict defining plot options for data visualization
            pdf_options: (optional) python dict defining plot options for pdf visualization
            Range: (optional) tuple defining a projection range for the plot
            Slice: (optional) python dict defining slices for other variables
            Bins: (optional) int defining number of bins to plot data
            isHistogram: (optional) Flag to plot data as a histogram

        """
        data_options = data_options if data_options is not None else {}
        pdf_options = pdf_options if pdf_options is not None else {}

        self._data_options = data_options
        self._pdf_options = pdf_options
        self._projection = projection

        self._x = pdf.x

        if not any([x.GetName() == projection for x in self._x]):
            raise ValueError(
                "wrong name of 'projection' variable. It must be coincides with the 'pdf' arguments!"
            )

        frame = ROOT.RooPlot
        for x in self._x:
            if x.GetName() == projection:
                if len(Range) == 0:
                    Range = tuple(x.getRange())
                if isinstance(title, str):
                    ti = title
                elif isinstance(title, tuple):
                    ti = title[0]
                frame = x.frame(Name=f"{x.GetName()} frame", Title=ti)
                break

        if Slice is not None:
            for k, v in Slice.items():
                if not isinstance(v, tuple):
                    raise TypeError("slice values must have 'tuple' type!")
                for i, x in enumerate(self._x):
                    if x.GetName() == k:
                        x.setRange("slice", *v)
                        # x.setRange('aux_slice_l', x.getMin(),v[0])
                        # x.setRange('aux_slice_r', v[1],x.getMax())
                        self._x[i] = x

        # {'r': 'kRed', 'b': 'kBlue', 'g': 'kGreen', 'y': 'kYellow', 'w': 'kWhite', 'k': 'kBlack', 'm': 'kMagenta', 'c': 'kCyan'}
        colors = {0: "r", 1: "m", 2: "g", 3: "b", 4: "c"}
        styles = {0: "--", 1: "-."}

        pdf_plotOn_options_set = {
            "Normalization",
            "LineStyle",
            "LineColor",
            "LineWidth",
            "FillColor",
            "NormRange",
        }

        if not pdf_options.keys() <= pdf_plotOn_options_set:
            print(pdf_options.keys())
            raise ValueError(
                "Please check plotOn options for PDF function. Some of them are incorrect or not added to the checklist!"
            )

        if Slice is not None:
            pdf_options["ProjectionRange"] = "slice"

        pdf_options["Name"] = pdf.name

        # pdf_plotOn_options_final = dict(Name=pdf.get_name(), ShiftToZero=False, LineStyle='-', LineColor='b', LineWidth=3, DrawOption='', FillColor='b', MoveToBack=False)
        # pdf_plotOn_options_final.update({k : pdf_options[k] for k in (pdf_plotOn_options_final.keys() & pdf_options.keys())})

        d = {
            k: v
            for k, v in self.get_object_map(pdf).items()
            if len(v.x_limits) == 1 and list(v.x_limits.keys())[0] == projection
        }

        components = []
        comp = True
        if len(d) == 1:
            comp = False
        for pdf_names, pdf_curr in d.items():
            pdf_name, pdf_mother_name, iden = pdf_names
            if not len(re.findall(r"\(\+\)|\(\*\)|\(X\)|\(\*\|\)", pdf_name)):
                print(pdf_name)
                components.append(pdf_curr)
            if len(re.findall(r"\(\*\)|\(X\)|\(\*\|\)", pdf_name)) or len(
                re.findall(r"\|\([a-z,]+\)", pdf_name)
            ):
                comp = False

        # data_plotOn_options_final = dict(Name=data.get_name(),
        #                                 DataError='Poisson',
        #                                 LineStyle='-',
        #                                 LineColor='k',
        #                                 LineWidth=3,
        #                                 MarkerStyle=21,
        #                                 MarkerColor='k',
        #                                 XErrorSize=1,
        #                                 DrawOption='',
        #                                 FillStyle=0)
        data_plotOn_options_set = {
            "DataError",
            "LineStyle",
            "LineColor",
            "LineWidth",
            "MarkerStyle",
            "MarkerColor",
            "XErrorSize",
            "DrawOption",
            "FillStyle",
            "Binning",
        }

        if len(data_options.keys()) > 8:
            raise TypeError(
                "Please shorten number of plotOn options for dataset because only 8 parameters is implemented at most!"
            )
        if not data_options.keys() <= data_plotOn_options_set:
            print(data_options.keys())
            raise ValueError(
                "Please check of plotOn options for dataset. Some of them are incorrect or not added to the checklist!"
            )

        # data_plotOn_options_final.update({k : data_options[k] for k in (data_plotOn_options_container & data_options.keys())})

        if Bins is not None:
            data_options["Binning"] = (Bins,) + Range
            data_options["FillStyle"] = 0
        if Slice is not None:
            data_options["CutRange"] = "slice"
        if isHistogram is True:
            data_options["DrawOption"] = "BX"

        data_options["Name"] = data.name

        data.dataset.plotOn(frame, **data_options)
        # If a PDF is plotted in a frame in which a dataset has already been plotted, it will show a projected
        # curve integrated over all variables that were present in the shown dataset except for the one on the x-
        # axis. The normalization of the curve will also be adjusted to the event count of the plotted dataset. An
        # informational message will be printed for each projection step that is performed
        pdf.function.plotOn(frame, **pdf_options)
        # pdf.get_function().plotOn(frame,ProjWData=data.get_dataset())

        if comp:
            for i, component in enumerate(components):
                pdf.function.plotOn(
                    frame,
                    Name=component.name,
                    LineStyle=styles[i % 2],
                    LineWidth=3,
                    LineColor=colors[i],
                    Components={component.function},
                )

        if isinstance(title, tuple):
            frame.GetXaxis().SetTitle(title[1])
            frame.GetYaxis().SetTitle(title[2])

        frame.GetYaxis().SetTitleOffset(1.4)
        self._frame = frame
        self._pdf = pdf
        self._data = data

    @property
    def frame(self):
        """Getter for frame."""
        return self._frame

    def set_paramOn(
        self,
        pdf_options: dict[str, Any] = {
            "ShowConstants": False,
            "Format": ("NE", ROOT.RooFit.AutoPrecision(1)),
            "Layout" : [0.65,0.85,0.9]
        },
    ) -> None:
        """Set parameter options to plot PDF.

        Args:
            pdf_options: (optional) python dict defining parameter options

        """
        pdf = self._pdf
        frame = self._frame
        pdf.function.paramOn(frame, **pdf_options)
        frame.getAttText().SetTextSize(0.03)
        self._frame = frame

    def set_statOn(self, stat_options: dict[str, Any] = {
              "Layout" : [0.15,0.35,0.9]
        }
    ) -> None:
        """Set statistics options to plot data.

        Args:
            stat_options: (optional python dict defining statistics options)

        """
        data = self._data
        frame = self._frame
        slice_option = {k: v for k, v in self._data_options.items() if k == "CutRange"}
        data.dataset.statOn(frame, **{**stat_options, **slice_option})
        frame.getAttText().SetTextSize(0.03)
        self._frame = frame

    def make_plot(
        self, filename: str = "plot", pdf_format: bool = True, log: bool = False
    ) -> None:
        """Make plot with data and PDF and save it to the rootfile and image file.

        Args:
            filename: string defining the file name
            pdf_format: (optional) flag defining pdf or png file is created
            log: (optional) flag defining Log scale for y-axis in the plot

        """
        frame = self._frame
        c = ROOT.TCanvas("canvas", "RooPlot Canvas", 800, 600)
        if log:
            c.SetLogy()
            frame.SetMinimum(0.1)
        ROOT.gPad.SetLeftMargin(0.15)
        frame.Draw()
        ext = ".pdf" if pdf_format else ".png"
        rootfile = filename + ".root"
        filename += ext
        c.SaveAs(filename)

        f = ROOT.TFile(rootfile, "RECREATE")
        c.Write("frame")
        f.Close()

    def make_pullplot(
        self, filename: str = "pull", pdf_format: bool = True, log: bool = False
    ) -> None:
        """Make plot and pull plot with data and PDF and save it to the image file.

        Args:
            filename: string defining the file name
            pdf_format: (optional) flag defining pdf or png file is created
            log: (optional) flag defining Log scale for y-axis in the plot

        """
        data = self._data
        pdf = self._pdf
        projection = self._projection
        frame = self._frame

        pullframe = None
        for x in self._x:
            if x.GetName() == projection:
                pullframe = x.frame(Title="Pull distribution")
                xmin, xmax = tuple(x.getRange())

        hpull = frame.pullHist(data.name, pdf.name)
        pullframe.addPlotable(hpull, "P")
        pullframe.SetMinimum(-5.0)
        pullframe.SetMaximum(+5.0)

        line_central = ROOT.TLine(xmin, 0.0, xmax, 0.0)
        line_central.SetLineColor(2)
        line_central.SetLineStyle(2)
        line_central.SetLineWidth(3)

        line_high = ROOT.TLine(xmin, 3.0, xmax, 3.0)
        line_high.SetLineColor(2)
        line_high.SetLineStyle(2)
        line_high.SetLineWidth(2)

        line_low = ROOT.TLine(xmin, -3.0, xmax, -3.0)
        line_low.SetLineColor(2)
        line_low.SetLineStyle(2)
        line_low.SetLineWidth(2)

        pullframe.GetYaxis().SetTitle("Pull(#sigma)")

        c = ROOT.TCanvas("canvas", "canvas", 800, 600)
        if log:
            c.SetLogy()
            frame.SetMinimum(0.1)
        c.Divide(1, 2)
        c.cd(1).SetPad(0.005, 0.2525, 0.995, 0.995)
        frame.Draw()
        c.cd(2).SetPad(0.005, 0.005, 0.995, 0.2525)
        pullframe.Draw()
        line_central.Draw("SAME")
        line_low.Draw("SAME")
        line_high.Draw("SAME")
        ext = ".pdf" if pdf_format else ".png"
        filename += ext
        c.SaveAs(filename)

    def make_smart_binning(self) -> bool:
        """Make plot with adjusted bins."""
        pass

    # Slice option is irrelevant for 2D plot
    def make_2d_plot(
        self, name: str = "", filename: str = "2dplot", pdf_format: bool = True
    ) -> None:
        """Make 2-dimensional plot for 2-dimensional PDF.

        Args:
            name: (optional) string defining global title of the plot
            filename: string defining the file name
            pdf_format: (optional) flag defining pdf or png file is created

        """
        pdf = self._pdf
        if not len(self._x) == 2:
            raise AttributeError(
                "Wrong number of arguments for pdf provided. Only two arguments in total is supported"
            )
        x, y = tuple(self._x)
        hh_model = pdf.function.createHistogram(
            name, x, Binning=50, YVar=dict(var=y, Binning=50)
        )
        hh_model.SetLineColor(ROOT.kBlue)

        c = ROOT.TCanvas("canvas", "canvas", 800, 600)
        ROOT.gPad.SetLeftMargin(0.20)
        hh_model.SetTitle(name)
        hh_model.GetZaxis().SetTitleOffset(2.5)
        hh_model.GetXaxis().SetTitleOffset(2)
        hh_model.GetYaxis().SetTitleOffset(2)
        hh_model.Draw("surf1")
        ext = ".pdf" if pdf_format else ".png"
        filename += ext
        c.SaveAs(filename)

    # Calculate and return reduced chi-squared (neyman ?)
    # between a last added curve and a histogram (total ones by default in constructor)
    # in a RooPlot 'frame' object
    def get_chi2(self) -> float:
        """Calculate reduced chi-2 between a curve and data histogram."""
        frame = self._frame
        pdf = self._pdf
        return frame.chiSquare(pdf.get_NFitFloated())


# ========== Simple examples for the module ==========
if __name__ == "__main__":
    # x-dim PDF as a sum of two PDFs
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

    # y-dim PDF as a convolution of two PDFs
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

    # (x-y) uncorr. PDF product
    product = x_pdf * y_pdf

    # Toy data generation
    binned_data = RooFitData(
        "2D-binned-data",
        "binned",
        (product, 300000),
        product.x,
        bins=[50, 50],
        seed=1234,
    )

    # PDF product fit to data
    r = RooFitMaker(binned_data, product, "ML")
    r.dump_to_file()

    # Plot x-projection in y-slice (0.76-0.80)
    p = RooFitPlot(
        binned_data,
        product,
        "x",
        "x-projection in y-slice (0.76, 0.80)",
        Slice={"mom": (0.76, 0.80)},
    )
    p.set_statOn()
    p.set_paramOn()
    p.make_plot()
    p.make_pullplot()
    p.make_2d_plot()
