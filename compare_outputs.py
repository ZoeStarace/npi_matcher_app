import pandas as pd

# Load your app's output and the example output
your_output = pd.read_csv("test_output.csv")
example_output = pd.read_csv("example_output.csv")

# Optional: Sort both DataFrames by key columns for consistent comparison
sort_cols = ["First_Name_Supplied", "Last_Name_Supplied", "NPI"]  # adjust as needed
your_output = your_output.sort_values(by=sort_cols).reset_index(drop=True)
example_output = example_output.sort_values(by=sort_cols).reset_index(drop=True)

# Compare DataFrames
if your_output.equals(example_output):
    print("✅ The outputs match exactly!")
else:
    print("❌ The outputs do NOT match.")
    # Show differences
    diff = your_output.compare(example_output)
    print(diff)