import subprocess
import pandas as pd
import tempfile
import os

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    data = None
    if args.filename:
        with open(args.filename, "rb") as file:
            import pickle

            data = pickle.load(file)
    genome = "fmr1" if os.getenv("GENOME") is None else os.getenv("GENOME")

    def is_picklable(obj):
        try:
            pickle.dumps(obj)
            return True
        except:
            return False

    output_file = "final_output"
    if output_file:
        import pickle
        import matplotlib.pyplot as plt
        import types
        from inspect import currentframe

        frame = currentframe()
        variables = {
            k: v
            for k, v in frame.f_locals.copy().items()
            if is_picklable(v)
            and (
                not isinstance(v, types.FunctionType)
                or isinstance(v, types.MethodType)
                or isinstance(v, types.ModuleType)
            )
        }
        with open(output_file, "wb") as file:
            pickle.dump(variables, file)
