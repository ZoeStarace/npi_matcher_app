import pandas as pd

REQUIRED_COLUMNS = {"First Name", "Last Name", "Specialty", "Hospital"}

def validate_file(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, "Unsupported file format. Please upload CSV or Excel."
        
        if not REQUIRED_COLUMNS.issubset(set(df.columns)):
            missing = REQUIRED_COLUMNS - set(df.columns)
            return None, f"Missing required columns: {', '.join(missing)}"
        
        return df, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"