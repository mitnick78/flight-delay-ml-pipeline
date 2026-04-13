from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from config import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

def get_preprocessor():
    """
    Creates and returns a scikit-learn ColumnTransformer configured
    to preprocess numerical and categorical features for the flight delay prediction model.
    """
    # Preprocessing for numerical features
    # Impute missing values with median, then scale to have zero mean and unit variance
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # Preprocessing for categorical features
    # Impute missing values with a constant 'missing' (or most frequent), then one-hot encode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUMERICAL_FEATURES),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ]
    )

    return preprocessor
