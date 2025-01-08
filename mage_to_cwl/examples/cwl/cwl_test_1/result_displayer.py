import pickle
import os
import matplotlib.pyplot as plt
import argparse

def display_data(file_path):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    
    for var_name, var_value in data.items():
        if isinstance(var_value, plt.Figure):
            os.makedirs("./figures", exist_ok=True)
            plt.savefig(f"./figures/{var_name}.png")
        else:
            print(f"{var_name}: {var_value}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display data from a pickle file.")
    parser.add_argument('-f', '--file', required=True, help='Path to the pickle file')

    args = parser.parse_args()
    display_data(args.file)
