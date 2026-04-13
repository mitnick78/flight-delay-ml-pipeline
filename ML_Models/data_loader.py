import os
import sys
import pandas as pd

from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.connection import get_connection

from config import NUMERICAL_FEATURES, CATEGORICAL_FEATURES, TARGET_COLUMN, RANDOM_STATE, TEST_SIZE


def load_data():
    """
    Loads the gold_flights dataset for raw arrival-delay regression.
    """
    conn = get_connection()
    query = "SELECT * FROM gold_flights;"
    df = pd.read_sql(query, conn)
    conn.close()

    df = df.dropna(subset=[TARGET_COLUMN])
    return df


def get_train_test_split():
    """
    Loads the regression dataset and returns a train/test split.
    """
    df = load_data()

    features = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X = df[features].copy()
    y = df[TARGET_COLUMN].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    print(f"Loaded {len(df)} records for regression.")
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Testing set: {X_test.shape[0]} samples")

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    try:
        X_train, X_test, y_train, y_test = get_train_test_split()
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")
