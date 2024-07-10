import json
import numpy as np
from typing import Dict, List, Tuple
from matplotlib import pyplot as plt

from functions import calc_time_from_sweeps

FILES = files = {
    {%- for name, path in analysis.items() -%}"{{name}}": "{{path}}",{%- endfor -%} 
}


def run(): 
    """ Write your code here. 
    
    f.e. (avrg, inrow, single sweep):
        plot_single_analysis("2024-06-11avrg-0-23_0-0-2_t6Soma_sweeps")
    or (stacked): 
        plot_stacked_analysis("2024-06-11_stacked-0-23_0-0-2_t6Soma_sweeps")
    or (stack single sweeps): 
        sweeps = build_stacked(["2024-0-611_sweep-00_0-0-2_t6Soma_sweeps", "2024-06-11_sweep-13_0-0-2_t6Soma_seeps"])
        time = calc_time_from_sweeps(sweeps)
        plot_data("stacked-sweep00-sweep13", sweeps, time) 
    """
    # Write code here: 
    # ... 
    # ...

##### HELPER FUNCTIONS ##### 

def plot_single_analysis(name: str, ylim=None): 
    """ Plot avrg, inrow or single sweeps: 

    f.e.: 
        plot_single_analysis("2024-06-11_avrg-0-23_0-0-2_t6Soma_sweeps")
        plot_single_analysis("2024-06-11_inrow-0-23_0-0-2_t6Soma_sweeps")
        plot_single_analysis("2024-06-11_sweep-00_0-0-2_t6Soma_sweeps", ylim=(-50, -40))

    """
    sweeps, time = load_analysis(FILES[name])
    plot_data(name, sweeps, time*len(sweeps), ylim=ylim) 

def plot_stacked_analysis(name: str, ylim=None): 
    """ Plot stacked:
    Works just as `plot_single_analysis` but uses the simple time (time=time
    of first sweep) 

    f.e.: 
        plot_stacked_analysis("2024-06-11_stacked-0-23_0-0-2_t6Soma_sweeps")
    """
    sweeps, time = load_analysis(FILES[name])
    plot_data(name, sweeps, time, ylim=ylim) 

def build_stacked(names: List[str]) -> List[List[float]]: 
    """ Loads data from SINGLE sweeps (sweep-XX) and returns a list of all
    sweeps.

    NOTE: This ONLY works with single sweeps, i.e names ending with or paths
    including `sweep-<sweep-number>`, f.e.: 

    Then use f.e. like this: 
        sweeps = build_stacked(["2024-0-611_sweep-00_0-0-2_t6Soma_sweeps", "2024-06-11_sweep-13_0-0-2_t6Soma_seeps"])
        time = calc_time_from_sweeps(sweeps)
        plot_data("stacked-sweep00-sweep13", sweeps, time) 
    """
    sweeps = []
    for name in names: 
        data, _ = load_analysis(FILES[name]) 
        sweeps.append(data[0])
    return sweeps

def load_analysis(path: str) -> Tuple[List[List[float]], float]:
    """ Loads single analysis """
    with open(path, "r") as f: 
        sweeps = json.load(f) # Load data from json
        time = calc_time_from_sweeps(sweeps) # Calculate time
        return sweeps, time


#### PLOT DATA ####

def plot_data(
    path, values, total_time, ylim=None, min_peaks=None, max_peaks=None, df=None
):  
    """ Plots given data. 

    plot_data stores a .png at "{path}.png" and a .svg ag "{path}.svg"
    NOTE: To show plots, uncomment line 46 in extractor.plotting
    """
    num_values = len(values) if isinstance(values[0], float) else len(values[0])
    print("Plotting now: ", num_values, total_time)
    listxachs=np.linspace(0, total_time, num_values)
    # Plot peaks, if set
    if min_peaks is not None:
        plt.scatter(listxachs, min_peaks, c='b')
    if max_peaks is not None:
        plt.scatter(listxachs, max_peaks, c='b')
    print("building plot")
    if isinstance(values[0], float):
        plt.plot(listxachs, values, linewidth=0.3, color="red")
    else: 
        for i, xs in enumerate(values): 
            plt.plot(listxachs, xs, linewidth=0.3, color="red", label = 'id %s'%i)
    plt.xlabel("Time [minutes]",
            family = 'serif',
            color='black',
            weight = 'normal',
            size = 10,
            labelpad = 5)
    plt.ylabel("Voltage [mV]",
            family = 'serif',
            color='black',
            weight = 'normal',
            size = 10,
            labelpad = 5)
    if ylim:
        plt.ylim(ylim)
    # Store figure
    plt.savefig(f"{path}.png", format='png', dpi=90)  # Adjust dpi for lower resolution
    plt.savefig(f"{path}.svg", format='svg')    # only if you want to safe it
    # Store df (peaks)
    if df is not None:
        df.to_csv(f"{path}.csv")
    plt.show()
    plt.cla()
    plt.clf()
 
if __name__ == "__main__": 
    run()
