import os
from beep.structure import BiologicDatapath
from matplotlib import pyplot as plt

OUT_DIR = "ProcessedData"
IN_DIR = "TestData"
in_file_name = "230630_S0009_E0001_C02.csv"
in_file_name = "S0013_E0001_1_C06.txt"
this_dir = os.path.dirname(os.path.abspath(__file__))
cycler_file = os.path.join(this_dir, IN_DIR, in_file_name)
outfile = os.path.join(this_dir, OUT_DIR, in_file_name[:-4] + ".json")

biologic_metadata_path = os.path.join(this_dir, IN_DIR, "S0013_E0001_1_C06.mpl")
metadata = BiologicDatapath.parse_metadata(biologic_metadata_path)
print(metadata)

def handle_new_datapath(in_file, out_file):
    dp = BiologicDatapath.from_file(in_file)
    is_valid, msg = datapath.validate()
    print("File is valid: ", is_valid + ", Message: " + msg)
    dp.structure()
    # Write the processed file to disk, which can then be loaded.
    dp.to_json_file(out_file)
    return dp

try:
    datapath = BiologicDatapath.from_json_file(outfile)
except FileNotFoundError:
    datapath = handle_new_datapath(cycler_file, outfile)

reg_charge = datapath.structured_data[datapath.structured_data.step_type == 'charge']
print("Mean current for cycle 25: ", reg_charge.current[reg_charge.cycle_index == 25].mean())
print("Number of cycles: ", reg_charge.cycle_index.max())
print("Max charge capacity at cycle 25: ", reg_charge.charge_capacity[reg_charge.cycle_index == 25].max())

plt.title("capacity vs. voltage of charge cycle 40")
plt.plot(reg_charge.charge_capacity[reg_charge.cycle_index == 40], reg_charge.voltage[reg_charge.cycle_index == 40])
plt.show()

plt.title("Energy efficiency with growing cycles")
plt.plot(datapath.structured_summary.cycle_index, datapath.structured_summary.energy_efficiency)
plt.show()
