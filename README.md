# roofit_functional
roofit-functional is a python wrapper for RooFit C++ library which models the expected distribution of events in an elementary particle physics data analysis 

# Desription
All the probability density functions (PDFs) are constructed on the basis of step-to-step procedure. This procedure is based on elementary PDFs, which are
hard-coded in the frame of the RooFit C++ package.
Structure of the elementary PDFs could be sequentially complicated via four available actions: summation, multiplication, convolution and composition. 
Besides PDF function, an ordinary function (not normalized in the range of its arguments) could be also constructed. 

Let's consider actions for PDF functions in a more detail:

1. Summation of two or more PDF functions. This action is a straightforward. 


