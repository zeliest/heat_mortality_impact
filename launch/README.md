# Launch

This folder contains two subfolders, one for python scripts, the other for bash scripts. 

For each type, the model_run script runs the model to calculate the impacts, while the test_sensitivity allows to test
the role of the different uncertainties in the model (the only possible flexible arguments for the sensitivity analysis are the region, the time, the scenario and the number of runs). 

The bash script launches climada and allows to run the model from the terminal with different inputs, 
and the python script translate these inputs in python and calls the monte carlo impact calculation.
