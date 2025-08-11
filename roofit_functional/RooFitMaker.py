import ROOT
import sys
from pathlib import Path
from typing import Any, List


class RooFitMaker():
    def __init__(self, data, pdf, fittype : str, Range = "", ExternalConstraints = set(), Minos : bool = False, Hesse : bool = True):
        #'fittype' could be NLL (binned / unbinned) or chi2 (binned)
        
        #'Range' is Dict[str,Tuple] w/ key : x.GetName() and value : Tuple[x_low,x_high]
        # Only one range is implemented. Joint ranges are not supported here yet!
        if not isinstance(Range, (str,dict)):
            raise TypeError("wrong typer of parameter 'Range' provided. It must be 'str' or 'dict'")
        if isinstance(Range,dict):
            for k,v in Range.items():
                if v[0] >= v[1]:
                    raise ValueError(f"range of variable {k} is not correct!")
                for x in pdf.get_x():
                    if x.GetName() == k:
                        x.setRange("Range",*v)
            Range = "Range"

        if fittype == 'NLL':
            #construct NLL of pdf w.r.t data
            self._cost = pdf.get_function().createNLL(data.get_dataset(),Extended=pdf.get_extended(),GlobalObservables=pdf.get_x(),Range=Range,ExternalConstraints=ExternalConstraints)
#            self._cost = pdf.get_function().createNLL(data.get_dataset())
            #create RooFitResult object
            self._r = pdf.get_function().fitTo(data.get_dataset(),Extended=pdf.get_extended(),GlobalObservables=pdf.get_x(),Range=Range,Save=True,PrintLevel=-1,ExternalConstraints=ExternalConstraints,Minos=Minos,Hesse=Hesse)
#            self._r = pdf.get_function().fitTo(data.get_dataset(),Save=True,PrintLevel=-1)
        elif fittype == 'chi2':
            self._cost  = pdf.get_function().createChi2(data.get_dataset(),Extended=pdf.get_extended(),GlobalObservables=pdf.get_x(),Range=Range,ExternalConstraints=ExternalConstraints)
            self._r = pdf.get_function().chi2FitTo(data.get_dataset(),Extended=pdf.get_extended(),GlobalObservables=pdf.get_x(),Range=Range,Save=True,PrintLevel=-1,ExternalConstraints=ExternalConstraints,Minos=Minos,Hesse=Hesse)

        pdf.set_NFitFloated(len(list(self._r.floatParsFinal())))
        self._pdf = pdf

    def dump_to_file(self, ofile : str ="fitresult.txt"):
        ofile = Path(ofile)
        r = self._r
        cov = r.covarianceMatrix()
        cor = r.correlationMatrix()

        # Create temp file to fill in RooFitResult multilines
        f = ROOT.std.ofstream('temp')
#        self._cost.Print("v")
        r.printMultiline(f,1111,True)
        r.printValue(f)
        f.close()
        temp = Path('temp')

        # Create temp2 file to fill in separate values  from the fit
        orig = sys.stdout
        temp2 = Path('temp2')
        with temp2.open('w') as fi:
            sys.stdout = fi
            try:
                print('\n')
                print("Status : ", r.status())
                print("Error matrix quality : ", r.covQual())
                print("FCN : ", r.minNll())
                print("EDM :", r.edm())
                print("List of fixed parameters :", *[ v for v in r.constPars()], sep= '\n')
                print("List of floating parameters (Minos error, if ON)):", *[ v for v in r.floatParsFinal()], sep='\n')
                print("Covariance Matrix : ", *[ [ cov(raw,col) for col in range(cov.GetNcols()) ] for raw in range(cov.GetNrows())], sep ='\n')
                print("Correlation Matrix : ", *[ [ cor(raw,col) for col in range(cor.GetNcols()) ] for raw in range(cor.GetNrows())], sep ='\n')
                print("Hesse errors : ", *[ (x.GetName(),x.getError()) for x in r.floatParsFinal() ],sep='\n' )
            finally:
                sys.stdout = orig

        # Combine temp & temp2 to result 'ofile'
        with ofile.open('w') as ofi:
            for ifile in [temp,temp2]:
                with ifile.open('r') as ifi:
                    for line in ifi:
                        ofi.write(line)

        # Remove temp & temp2
        for ifile in [temp,temp2]:
            ifile.unlink()    

    def give_fit_results(self, Minos : bool = False):
        r = self._r
#        results = list(r.floatParsFinal()) + list(r.constPars())
        results = list(r.floatParsFinal())
        if not Minos:
            return {x.GetName() : [x.getValV(),x.getError()] for x in results}
        else:
            return {x.GetName() : [x.getValV(),(x.getErrorLo(),x.getErrorHi())] for x in results}

    def give_fit_quality(self):
        pdf = self._pdf
        r = self._r
        return {'Status' : r.status(), 'Quality' : r.covQual(), 'EDM' :r.edm()}

if __name__ == "__main__":
    from roofit_functional.RooFitFunction import RooFitFunction
    from roofit_functional.RooFitData import RooFitData

    # Delta E 1-dim RooFit function test
    de_cb = RooFitFunction('CrystalBall1',{'dE' : [-.15,.15]}, 'CrystalBall', {'x0CB' : [0,-0.01,0.01], 'sigmacbL': [0.02,0.005,0.05], 'sigmacbR': [0.02,0.005,0.05],
        'alphaL': [0.1,0.005,2], 'alphaR': [0.1,0.005,2], 'nL' : [1,0.1,20.], 'nR' : [1,0.1,20.]})
    de_bfGauss = RooFitFunction('Gauss',{'all' : de_cb}, 'BifurGauss' , {'x0' : [0,-0.01,0.01], 'sigmaL': [0.01,0.001,0.05], 'sigmaR': [0.01,0.001,0.05]})
    de_pdf = de_cb.get_add(de_bfGauss,{'frac': [0.5,0.,1.]})

    # Omega 1-dim RooFit function test
    mom_bw = RooFitFunction('BreitWigner', {'mom': [0.74,.855]}, 'BreitWigner', {'mean' : [0.78265,0,0], 'width' : [0.0085,0,0]})
    mom_cb = RooFitFunction('CrystalBall2', {'all' : mom_bw}, 'CrystalBall', {'mom_x0CB' : [0,0,0], 'mom_sigcbL' : [0.005,0.001,0.05], 'mom_sigcbR' : [0.005,0.001,0.05],
        'mom_alphaL' : [1,0.005,2], 'mom_alphaR' : [1,0.005,2], 'mom_nL' : [1,0.01,50.], 'mom_nR' : [1,0.01,50.]})
    mom_pdf  = mom_bw.get_convolution(mom_cb)

    # (Delta E - Omega) RooFit uncorr. product
    de_mom_uncorr = mom_pdf * de_pdf

#    data = de_mom_uncorr.get_function().generate(set(de_mom_uncorr.get_x()),100000)
    data = de_mom_uncorr.get_function().generate(set(de_mom_uncorr.get_x()),500000)
    binned_data = RooFitData("test","binned",data,de_mom_uncorr.get_x(),bins=[100,100])
    r = RooFitMaker(binned_data,de_mom_uncorr,"NLL")
    r.dump_to_file()
