import matplotlib.pyplot as plt
import numpy as np

def calculate_travel_time(start, end, mode):
    distances = {
        ('A', 'B'): 450,
        ('B', 'C'): 650,
        ('A', 'C'): 1100
    }
    
    distance = distances.get((start, end)) or distances.get((end, start))
    
    if mode == 'shuttle':
        return round(distance / 500)
    elif mode == 'bike':
        return round(distance / 166.67)
    elif mode == 'walk':
        return round(distance / 70.62)
    
def convert_to_time_label(ticks):
    labels = ['6AM', '8AM', '10AM', '12PM', '2PM', '4PM', '6PM']
    return [labels[int(tick // 120)] if tick < 720 else '6PM' for tick in ticks]

def plot_results(results, times, rates):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('APC Campus Bike Sharing System Model', fontsize=16)

    # Arrival Rate
    axs[0, 0].plot(range(len(times)), rates)
    axs[0, 0].set_title('Arrival Rate over Time')
    axs[0, 0].set_xlabel('Time Step')
    axs[0, 0].set_ylabel('Arrival Rate')
    axs[0, 0].set_xticks([0, 120, 240, 360, 480, 600, 720])
    axs[0, 0].set_xticklabels(convert_to_time_label([0, 120, 240, 360, 480, 600, 720]))
    axs[0, 0].lines[0].set_color('k')

    # Average Waiting Time
    # axs[0, 1].plot(results["Average Waiting Time"])
    # axs[0, 1].set_title("Average Waiting Time")
    # axs[0, 1].set_xlabel("Time (minutes)")
    # axs[0, 1].set_ylabel("Minutes")
    # axs[0, 1].set_xticks([0, 120, 240, 360, 480, 600, 720])
    # axs[0, 1].set_xticklabels(convert_to_time_label([0, 120, 240, 360, 480, 600, 720]))
    # axs[0, 1].lines[0].set_color('k')

    # Average Waiting Time
    avg_waiting_time = np.array(results["Average Waiting Time"])
    valid_indices = ~np.isnan(avg_waiting_time)
    axs[0, 1].plot(np.arange(len(avg_waiting_time))[valid_indices], avg_waiting_time[valid_indices], color='k', marker='o')
    axs[0, 1].set_title("Average Waiting Time")
    axs[0, 1].set_xlabel("Time (minutes)")
    axs[0, 1].set_ylabel("Minutes")
    axs[0, 1].set_xticks([0, 120, 240, 360, 480, 600, 720])
    axs[0, 1].set_xticklabels(convert_to_time_label([0, 120, 240, 360, 480, 600, 720]))

    # Queue Lengths
    axs[1, 0].plot(results["Queue Length A"], label="at Lapu-lapu cor.")
    axs[1, 0].plot(results["Queue Length B"], label="at Victoria cor.")
    axs[1, 0].plot(results["Queue Length C"], label="at APC")
    axs[1, 0].set_title("Queue Lengths")
    axs[1, 0].set_xlabel("Time (minutes)")
    axs[1, 0].set_ylabel("Number of People")
    axs[1, 0].legend()
    axs[1, 0].set_xticks([0, 120, 240, 360, 480, 600, 720])
    axs[1, 0].set_xticklabels(convert_to_time_label([0, 120, 240, 360, 480, 600, 720]))

    # Available Bikes
    axs[1, 1].plot(results["Bikes at A"], label="at Lapu-lapu cor.")
    axs[1, 1].plot(results["Bikes at B"], label="at Victoria cor.")
    axs[1, 1].plot(results["Bikes at C"], label="at APC")
    axs[1, 1].set_title("Available Bikes")
    axs[1, 1].set_xlabel("Time (minutes)")
    axs[1, 1].set_ylabel("Number of Bikes")
    axs[1, 1].legend()
    axs[1, 1].set_xticks([0, 120, 240, 360, 480, 600, 720])
    axs[1, 1].set_xticklabels(convert_to_time_label([0, 120, 240, 360, 480, 600, 720]))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()