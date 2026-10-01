import argparse
from pathlib import Path
import numpy as np

def validate_dataset(data_dir: Path):
    runs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("real_")]
    if not runs:
        print("No processed runs found in directory.")
        return

    print("="*50)
    print(f"DATA VALIDATION REPORT: {data_dir.name}")
    print("="*50)
    print(f"Total Usable Initializations: {len(runs)}")

    invalid_shapes = 0
    total_nans = 0
    total_infs = 0
    
    ye_stats = []
    yb_pos = []
    
    ch_stats = [[] for _ in range(10)]
    
    for run in runs:
        try:
            X = np.load(run / "X.npy")
            Yb = np.load(run / "Yb_true.npy")
            Ye = np.load(run / "Ye_true.npy")
            
            # Shape checks
            if X.shape != (10, 10, 128, 128) or Yb.shape != (10, 4, 128, 128) or Ye.shape != (10, 4, 128, 128):
                invalid_shapes += 1
                continue
                
            total_nans += np.isnan(X).sum() + np.isnan(Yb).sum() + np.isnan(Ye).sum()
            total_infs += np.isinf(X).sum() + np.isinf(Yb).sum() + np.isinf(Ye).sum()
            
            ye_stats.append(Ye.mean(axis=(0,2,3))) # mean error per variable
            yb_pos.append(Yb.mean(axis=(0,2,3)))   # positive rate per variable
            
            for c in range(10):
                ch_stats[c].append([X[:, c].min(), X[:, c].max(), X[:, c].mean(), X[:, c].std()])
                
        except Exception as e:
            print(f"Error reading {run.name}: {e}")
            invalid_shapes += 1

    print(f"\n[INTEGRITY CHECKS]")
    print(f"Invalid Shapes: {invalid_shapes}")
    print(f"NaN Count     : {total_nans}")
    print(f"Inf Count     : {total_infs}")
    
    if len(runs) > invalid_shapes:
        print(f"\n[X CHANNEL STATISTICS (NORMALIZED)]")
        print(f"{'Ch':<4} | {'Min':<8} | {'Max':<8} | {'Mean':<8} | {'Std':<8}")
        print("-" * 50)
        ch_codes = ["t2m", "tp", "z500", "u850", "v850", "ws850", "cape", "mslp", "z500_anom", "shr"]
        for c in range(10):
            arr = np.array(ch_stats[c])
            print(f"{ch_codes[c]:<4} | {arr[:,0].min():8.2f} | {arr[:,1].max():8.2f} | {arr[:,2].mean():8.2f} | {arr[:,3].mean():8.2f}")
            
        print(f"\n[LABEL STATISTICS]")
        print(f"{'Var':<6} | {'Mean Ye':<8} | {'Bust Rate (Yb)':<15}")
        print("-" * 50)
        var_codes = ["t2m", "tp", "z500", "ws850"]
        ye_arr = np.array(ye_stats).mean(axis=0)
        yb_arr = np.array(yb_pos).mean(axis=0)
        for v in range(4):
            print(f"{var_codes[v]:<6} | {ye_arr[v]:8.2f} | {yb_arr[v]*100:6.2f}%")
            
    print("\nValidation Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()
    validate_dataset(Path(args.data_dir))
