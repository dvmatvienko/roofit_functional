import ROOT
from pathlib import Path
from typing import Any, List, Tuple, Union
import re

class RooFitPlot:
    @staticmethod
    def get_object_map(pdf, pdf_mother = None, d = None, level = 0):
        if pdf_mother == None and d == None:
            d = {}
            pdf_mother = pdf
        d[(pdf.get_function_type(),pdf_mother.get_function_type(),level)] = pdf
        functionality = pdf.get_functionality()
        if isinstance(functionality,list):
            for i in range(len(functionality)):
                if isinstance(functionality[i],type(pdf)):
                    RooFitPlot.get_object_map(pdf.get_functionality()[i], pdf_mother = pdf, d = d, level = i)
                elif isinstance(functionality[i],dict):
                    RooFitPlot.get_object_map(list(pdf.get_functionality()[i].keys())[0], pdf_mother = pdf, d = d, level = i)
        return d

    def __init__(self, data, pdf, projection : str, title, data_options : dict = {}, pdf_options : dict = {}, Range : Tuple = tuple(), Bins = None):
        self._data = data
        self._data_options = data_options
        self._pdf = pdf
        self._pdf_options = pdf_options
        self._projection = projection

        if not any([x == projection for x in pdf.get_x_limits().keys()]):
            raise ValueError("worng name of 'projection' variable. It must be coincides with the 'pdf' arguments!")

        frame = None
        for x in pdf.get_x():
            if x.GetName() == projection:
                if len(Range) == 0:
                        Range = tuple(pdf.get_x_limits()[projection])
                if isinstance(title,str):
                      ti = title
                elif isinstance(title,tuple):
                      ti = title[0]
                if Bins == None:
                    frame = x.frame(Name="frame",Title=ti,Range=Range)
                elif isinstance(Bins,int):
                    frame = x.frame(Name="frame",Title=ti,Range=Range,Bins=Bins)
                break

        #{'r': 'kRed', 'b': 'kBlue', 'g': 'kGreen', 'y': 'kYellow', 'w': 'kWhite', 'k': 'kBlack', 'm': 'kMagenta', 'c': 'kCyan'}
        colors = {0 : 'r', 1 : 'b', 2 : 'g', 3 : 'm', 4 : 'c'}
        styles = {0 : '--', 1 : '--'}
        pdf_plotOn_options_final = dict(Name=pdf.get_name(), ShiftToZero=False, LineStyle='-', LineColor='b', LineWidth=3, DrawOption='', FillColor='b', MoveToBack=False)
        pdf_plotOn_options_final.update({k : pdf_options[k] for k in (pdf_plotOn_options_final.keys() & pdf_options.keys())})

        d = {k : v for k,v in self.get_object_map(pdf).items() if len(v.get_x_limits()) == 1 and list(v.get_x_limits().keys())[0] == projection}

        components = []
        comp = True
        if len(d) == 1:
            comp = False
        for pdf_names, pdf_curr in d.items():
            pdf_name, pdf_mother_name, iden = pdf_names 
            if not len(re.findall(r'\(\+\)|\(\*\)|\(X\)|\(\*\|\)',pdf_name)):
                print(pdf_name)
                components.append(pdf_curr)
            if len(re.findall(r'\(\*\)|\(X\)|\(\*\|\)',pdf_name)) or len(re.findall(r'\|\([a-z,]+\)',pdf_name)):
                comp = False

        data_plotOn_options_final = dict(Name=data.get_name(), DataError='Poisson', LineStyle='-', LineColor='k', LineWidth=3, MarkerStyle=21, MarkerColor='k', XErrorSize=1)
        data_plotOn_options_final.update({k : data_options[k] for k in (data_plotOn_options_final.keys() & data_options.keys())})

        data.get_dataset().plotOn(frame,**data_plotOn_options_final)
#        data.get_dataset().plotOn(frame)
        pdf.get_function().plotOn(frame,**pdf_plotOn_options_final)
#        pdf.get_function().plotOn(frame,ProjWData=data.get_dataset())

        if comp:
            for i,component in enumerate(components):
                print(component.get_function_type())
                pdf.get_function().plotOn(frame, Name=component.get_name(), LineStyle=styles[i%2], LineWidth=3, LineColor=colors[i], Components={component.get_function()})

        if isinstance(title,tuple):
            frame.GetXaxis().SetTitle(title[1])
            frame.GetYaxis().SetTitle(title[2])
        
        frame.GetYaxis().SetTitleOffset(1.4)
        self._frame = frame

    def get_frame(self):
        return self._frame

    def set_paramOn(self,pdf_options : dict = {}):
        pdf = self._pdf
        frame = self._frame
        pdf.get_function().paramOn(frame,**pdf_options)

    def set_statOn(self,stat_options : dict = {}):
        data = self._data
        frame = self._frame
        data.statOn(frame,**stat_options)

    def make_plot(self,filename='file.pdf',rootfile='file.root',log=False):
        frame = self._frame
        c = ROOT.TCanvas("canvas","canvas",800,600)
        if log: 
            c.SetLogy()
            frame.SetMinimum(0.1)
        ROOT.gPad.SetLeftMargin(0.15)
        frame.Draw()
        c.SaveAs(filename)

        f = ROOT.TFile(rootfile,"RECREATE")
        frame.Write()
        f.Close()

    def make_pullplot(self,filename='pull.pdf',rootfile='pull.root',log=False):
        data = self._data
        pdf = self._pdf
        projection = self._projection
        frame = self._frame

        pullframe = None
        for x in pdf.get_x():
           if x.GetName() == projection:
               pullframe = x.frame(Title="Pull distribution")

        hpull = frame.pullHist(data.get_name(),pdf.get_name())
        pullframe.addPlotable(hpull,"P")
        pullframe.SetMinimum(-5.)
        pullframe.SetMaximum(+5.)

        xmin, xmax = tuple(pdf.get_x_limits()[projection])

        line_central = ROOT.TLine(xmin,0.0,xmax,0.0)
        line_central.SetLineColor(2)
        line_central.SetLineStyle(2)
        line_central.SetLineWidth(3)

        line_high = ROOT.TLine(xmin,3.0,xmax,3.0)
        line_high.SetLineColor(2)
        line_high.SetLineStyle(2)
        line_high.SetLineWidth(2)

        line_low = ROOT.TLine(xmin,-3.0,xmax,-3.0)
        line_low.SetLineColor(2)
        line_low.SetLineStyle(2)
        line_low.SetLineWidth(2)

        pullframe.GetYaxis().SetTitle("Pull(#sigma)")

        c = ROOT.TCanvas("canvas","canvas",800,600)
        if log:
            c.SetLogy()
            frame.SetMinimum(0.1)
        c.Divide(1,2)
        c.cd(1).SetPad(0.005,0.2525,0.995,0.995)
        frame.Draw()
        c.cd(2).SetPad(0.005,0.005,0.995,0.2525);
        pullframe.Draw();
        line_central.Draw("SAME");
        line_low.Draw("SAME");
        line_high.Draw("SAME");
        c.SaveAs(filename)
        
    def make_smart_binning(self):    
        pass

    def make_2d_plot(self, name : str = '', filename = '2dplot.pdf'):
        pdf = self._pdf
        if not len(pdf.get_x()) == 2:
            raise AttributeError("Wrong number of arguments for pdf provided. It must be equal two")
        x, y = tuple(pdf.get_x())
        hh_model = pdf.get_function().createHistogram(name, x, ROOT.RooFit.Binning(50), ROOT.RooFit.YVar(y, ROOT.RooFit.Binning(50)))
        hh_model.SetLineColor(ROOT.kBlue)
    
        c = ROOT.TCanvas("canvas","canvas",800,600)
        ROOT.gPad.SetLeftMargin(0.20)
        hh_model.SetTitle(name)
        hh_model.GetZaxis().SetTitleOffset(2.5)
        hh_model.GetXaxis().SetTitleOffset(2)
        hh_model.GetYaxis().SetTitleOffset(2)
        hh_model.Draw("surf")
        c.SaveAs(filename)


if __name__ == "__main__":
    from RooFitFunction import RooFitFunction, RooFitVar
    from RooFitData import RooFitData
    from RooFitMaker import RooFitMaker

    # Delta E 1-dim RooFit function test
    de_pdf = RooFitFunction('CrystalBall',{'dE' : [-.15,.15]}, '2sidedCB', {'x0CB' : [0,-0.01,0.01], 'sigmacbL': [0.03,0.001,0.05], 'sigmacbR': [0.01,0.001,0.05],
        'alphaL': [0.1,0.005,10], 'nL' : [1,0.1,20.], 'alphaR': [0.1,0.005,10], 'nR' : [1,0.1,20.]})
#    de_bfGauss = RooFitFunction('Gauss',{'dE' : [-.15,.15]}, 'BFGauss' , {'x0' : [0,-0.01,0.01], 'sigmaL': [0.02,0.01,0.05], 'sigmaR': [0.02,0.01,0.05]})
#    de_pdf = de_cb.get_add(de_bfGauss,{'frac': [0.5,0.,1.]})

    # Omega 1-dim RooFit function test
    mom_bw = RooFitFunction('BreitWigner', {'mom': [0.74,0.87]}, 'BreitWigner', {'mean' : [0.78,0,0], 'width' : [0.0085,0,0]})
#    mom_Gauss = RooFitFunction('MGauss', {'mom' : [0.74,0.87]}, 'Gauss', {'mmeang' : [0,0,0], 'msigmag': [0.007,0.001,0.01]})
#    mom_pdf  = mom_bw.get_convolution(mom_Gauss,"test")

    # (Delta E - Omega) RooFit uncorr. product
    de_mom_uncorr = de_pdf*mom_bw

    data = de_mom_uncorr.get_function().generate(set(de_mom_uncorr.get_x()),100000)
    binned_data = RooFitData("test","binned",data,de_mom_uncorr.get_x())
    r = RooFitMaker(binned_data,de_mom_uncorr,"NLL")
    r.dump_to_file()
    p = RooFitPlot(binned_data,de_mom_uncorr,"dE","Test plot")
    p.make_plot()
    p.make_pullplot()
    p.make_2d_plot()

