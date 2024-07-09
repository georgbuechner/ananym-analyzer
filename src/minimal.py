import os 
import json

from extractor.functions import calc_time_from_sweeps
from extractor.plotting import plot_data 

def run(): 
    # All files from project/analysis 
    files = {
        "20240627_002_t5Soma_sweep-00": 
        "data/analysis/2024-06-27/0-0-2_t5Soma_sweeps/sweep-00_0-0-2_t5Soma_sweeps.json", 
        "2024-06-27/0-0-2_t5Soma_sweeps/sweep-22":
        "data/analysis/2024-06-27/0-0-2_t5Soma_sweeps/sweep-22_0-0-2_t5Soma_sweeps.json"
    }

    # NOTE: data (even single sweeps, i.e. sweep-XX) is stored as sweeps, t.i. a
    # list of lists. 
    with open(files["20240627_002_t5Soma_sweep-00"], "r") as f: 
        sweeps = json.load(f)
        time = calc_time_from_sweeps(sweeps)

        ylim = None # alternatively set ylim to f.e.: `ylim = (-50, -40)`
        path = "20240627_002_t5Soma_sweep" # Use any path.
        # plot_data stores a .png at "{path}.png" and a .svg ag "{path}.svg"
        # NOTE: To show plots, uncomment line 46 in extractor.plotting
        plot_data(path, sweeps, time, ylim=ylim) 
    

if __name__ == "__main__": 
    run()
