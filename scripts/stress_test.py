import time
import os
import sys
import numpy as np

# Ensure backend path is included
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.ml.inference import InferenceRunner
import torch

def run_stress_test():
    print("Starting stress test...")
    runner = InferenceRunner()
    
    # Generate dummy input tensor
    X = torch.zeros(1, 10, 10, 128, 128, dtype=torch.float32)
    
    latencies = []
    
    for i in range(25):
        t0 = time.perf_counter()
        _ = runner.run_inference(X)
        t1 = time.perf_counter()
        latencies.append(t1 - t0)
        
    latencies = np.array(latencies)
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    
    print(f"25 inferences completed.")
    print(f"p50 latency: {p50:.3f} s")
    print(f"p95 latency: {p95:.3f} s")
    
    if p95 > 2.0:
        print("FAIL: p95 latency exceeded 2.0s!")
        sys.exit(1)
        
    print("STRESS TEST OK.")

if __name__ == "__main__":
    run_stress_test()
