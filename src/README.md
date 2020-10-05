# Source Code for the Model

The write_entities folder contains the three python files to write the hazards, exposures and impact functions
into CLIMADA

The impact_calculation folder contains the calculate_impact.py file which calculates the impact once, and the 
impact_monte_carlo_parallel.py which calls the calculate_impact.py multiple times in parallel to do the monte carlo.

The util folder contains functions to plot the impacts and to get the impacts for cantons by using shapefiles.
