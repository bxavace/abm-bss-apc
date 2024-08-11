import warnings
from model import *
from agents import *
from helper import *

warnings.filterwarnings("ignore")

def run_model(days=1):
    model = TransportationModel()
    for _ in range(720 * days): 
        model.step()
    times, rates = model.get_arrival_rates()
    results = model.datacollector.get_model_vars_dataframe()
    return results, times, rates

if __name__ == '__main__':
    results = run_model(1)
    plot_results(*results)
    print(results[0].describe())