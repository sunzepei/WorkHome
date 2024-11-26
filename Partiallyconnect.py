## This code simulate Partially connected vehicles environment
## The vehicle distance is 50m, number of vehicles is 70, the entire length is 3450m(equally placed)
## The communication range is 500m which is 10 vehicles
## Simulation loop is the same, sub-channel selection
## Only different is the collision detection part.
##



import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import function as f
from scipy.interpolate import interp1d
# Simulation parameters
num_vehicles = 10
communication_range = 3 # Number of vehicles ahead and behind within communication range
num_subchannels = 15
num_subframes = 200
sps_interval_range = (5,16)
sliding_window_size = 10
counting_interval = 1000
reselection_probability = 0.2
# Variables to store PRR values
prr_values = []
cumualtive_prr_value = []
cumulative_prr_sum = 0
prr_count = 0
min_percent = 0.2
threshold = 3

# Initialize vehicle information
vehicles_info = {}
for vehicle in range(num_vehicles):
    # Define each vehicle's neighbor range based on the communication range
    start_idx = max(0, vehicle - communication_range)
    end_idx = min(num_vehicles - 1, vehicle + communication_range)
    neighbors = list(range(start_idx, end_idx + 1))
    # neighbors.remove(vehicle)  # Exclude self in the function already

    vehicles_info[vehicle] = {
        'neighbors': neighbors,
        'current_subchannel': np.random.choice(num_subchannels),
        'next_selection_frame': 0,
        'sps_counter': np.random.randint(sps_interval_range[0], sps_interval_range[1]),
        # Local resource map for the last 10 subframes sliding window
        'resource_map': np.zeros((num_subchannels, sliding_window_size), dtype=np.uint8),
        'successful_transmissions': []  # List to track successful transmission subframe
        }

# for vehicle, info in vehicles_info.items():
#     print(f"Vehicle {vehicle} neighbors: {info['neighbors']}")

# for vehicle, info in vehicles_info.items():
#     print(f"Vehicle {vehicle} SPS_Counter: {info['sps_counter']}")

sum_up = 0
for vehicle, info in vehicles_info.items():
    sum_up = sum_up + len(info['neighbors'])
print(f"the number of neighbor update is {sum_up - num_vehicles}")


total_neighbors = sum(len(info['neighbors']) for info in vehicles_info.values()) - num_vehicles


# Main simulation loop
for subframe in tqdm(range(num_subframes), desc="Processing", ncols=100):
    # Step 1: Allocate subchannels for vehicles and populate attempted transmissions
    attempted_transmissions = {}  # Track subchannel usage in the current subframe
    successful_transmissions = {}  # Track successful transmissions in the current subframe
    # Allocate subchannels and populate attempted_transmissions

    subframe_position = subframe % sliding_window_size
    for vehicle in vehicles_info:
        vehicles_info[vehicle]['resource_map'][:, subframe_position] = 0  # Reset current sub-frame


    for vehicle, info in vehicles_info.items():
        # print(f"Now is processing vehicle {vehicle}")
         # Handle SPS counter and reselection
        if subframe == info['next_selection_frame']:
            if info['sps_counter'] <= 0:
                if np.random.rand() < reselection_probability:
                # Randomly reselect subchannel if the interval has elapsed
                    info['current_subchannel'] = f.choose_subchannel(info['current_subchannel'],
                                                                            info['resource_map'],threshold)
                info['sps_counter'] = np.random.randint(sps_interval_range[0], sps_interval_range[1])
            else:
                pass

            f.update_neighbors(vehicle, info['current_subchannel'], vehicles_info,subframe_position)
            info['sps_counter'] -= 1
            # print(f"the {vehicle} counter is {info['sps_counter']}")
            info['next_selection_frame'] = subframe + 1

       # Track attempted transmissions
        current_channel = info['current_subchannel']
        if current_channel not in attempted_transmissions:
            attempted_transmissions[current_channel] = []
        attempted_transmissions[current_channel].append(vehicle)

    transmissions = f.package_received(attempted_transmissions,successful_transmissions,vehicles_info)
    success_num = sum(len(value) for value in transmissions.values())

    f.store_IPG(transmissions, vehicles_info,subframe)
    # Step 3: Calculate Packet Delivery Ratio (PDR) every 2000 subframes
    if subframe % counting_interval == 0 and subframe != 0:
        prr = f.calculate_PRR(success_num, total_neighbors)
        cumulative_prr_sum += prr
        prr_count += 1
        cumulative_prr = cumulative_prr_sum / prr_count
        cumualtive_prr_value.append(cumulative_prr)
    
    # print(attempted_transmissions)
    # print(total_successful_transmissions)


for vehicle, info in vehicles_info.items():
    print(f"Vehicle {vehicle} successful transmissions): {info['successful_transmissions']}")
          
# ipg_list = []
# # Calculate IPG for each vehicle
# for vehicle, info in vehicles_info.items():
#     # print(info['sps_counter'])
#     successful_transmissions = info['successful_transmissions']
#     # print(f'{vehicle}: {successful_transmissions}')
#     for i in range(1, len(successful_transmissions)):
#         ipg = successful_transmissions[i] - successful_transmissions[i - 1]
#         ipg_list.append(ipg)

# # Calculate the CCDF for IPG
# ipg_array = np.array(ipg_list)
# ipg_sorted = np.sort(ipg_array) * 100  # Convert sub-frames to milliseconds (assuming 1 sub-frame = 100 ms)
# unique_value, counts = np.unique(ipg_sorted, return_counts= True)

# cdf = np.cumsum(counts)/len(ipg_sorted)
# ccdf = 1 - cdf
# target_ccdf = 10 ** -5
# interpolator = interp1d(ccdf, unique_value, fill_value="extrapolate")
# x_value_at_target_ccdf = interpolator(target_ccdf)
# print(f"X-axis value at CCDF = 10^-5 : {x_value_at_target_ccdf}")

# # Plotting the CCDF of IPG
# plt.figure(figsize=(15, 8))
# plt.plot(unique_value, ccdf, label='CCDF of IPG')
# plt.xlabel('Inter-Packet Gap (IPG) [ms]')
# plt.ylabel('CCDF')
# plt.yscale('log')  # Set y-axis to logarithmic scale
# plt.title('CCDF of Inter-Packet Gap (IPG)')
# plt.legend()
# plt.grid(True)

# print(prr_values)
# Plot PDR over time
# plt.figure(figsize=(10, 6))
# plt.plot(cumualtive_prr_value, label='PRR over Time')
# plt.xlabel('Number of PRR values')
# plt.ylabel('Packet Received Ratio (PRR)')
# plt.title('PRR Trend Over Time')
# plt.legend()
# plt.grid(True)
# plt.show()