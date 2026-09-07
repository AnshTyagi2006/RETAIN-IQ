import pandas as pd
from sklearn.model_selection import train_test_split



df = pd.read_csv("data/processed/ecommerce_churn_clean.csv")

X = df.drop(columns=["customer_id", "churn"])
y = df["churn"]

X_train , X_test , y_train , y_test = train_test_split(
    X , y , 
    test_size = 0.2,
    random_state = 42,
    stratify = y
)

# print("X_train:", X_train.shape)
# print("X_test :", X_test.shape)

# print("y_train:", y_train.shape)
# print("y_test :", y_test.shape)

# print("\nTrain distribution:")
# print(y_train.value_counts(normalize=True).mul(100).round(2))

# print("\nTest distribution:")
# print(y_test.value_counts(normalize=True).mul(100).round(2))

numerical_columns_with_missing = [
    "tenure",
    "warehouse_to_home",
    "hour_spend_on_app",
    "order_count",
    "days_since_last_order",
    "order_amount_hike_from_last_year",
    "coupon_used"
]

# print(X_train[numerical_columns_with_missing].isnull().sum())

from sklearn.impute import SimpleImputer

imputer = SimpleImputer(strategy="median")
imputer.fit(X_train[numerical_columns_with_missing])
# print(imputer.statistics_)

X_train[numerical_columns_with_missing] = imputer.transform(
    X_train[numerical_columns_with_missing]
)

X_test[numerical_columns_with_missing] = imputer.transform(
    X_test[numerical_columns_with_missing]
)
# print(X_train[numerical_columns_with_missing].isnull().sum())
# print(X_test[numerical_columns_with_missing].isnull().sum())

categorical_columns = [
    "preferred_login_device",
    "preferred_payment_mode",
    "gender",
    "preferred_order_category",
    "marital_status"
]

from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder( handle_unknown="ignore" , sparse_output=False)
encoder.fit(X_train[categorical_columns])
# print(encoder.categories_)
X_train_encoded = encoder.transform( X_train[categorical_columns])
X_test_encoded = encoder.transform( X_test[categorical_columns])
# print(X_train_encoded.shape)
# print(X_train_encoded[:5])

encoded_feature_names = encoder.get_feature_names_out(
    categorical_columns
)

# print(encoded_feature_names)

numerical_columns = [
    "tenure",
    "warehouse_to_home",
    "hour_spend_on_app",
    "number_of_device_registered",
    "number_of_address",
    "order_amount_hike_from_last_year",
    "coupon_used",
    "order_count",
    "days_since_last_order",
    "cashback_amount"
]

from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
scaler.fit(X_train[numerical_columns])
# print(scaler.mean_)
# print(scaler.scale_)
X_train[numerical_columns] = scaler.transform( X_train[numerical_columns])
X_test[numerical_columns] = scaler.transform(
    X_test[numerical_columns]
)
# print(X_train[numerical_columns].head())

ordinal_columns = [
    "city_tier",
    "satisfaction_score",
    "complain"
]

from sklearn.compose import ColumnTransformer

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_columns),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_columns)
    ],
    remainder="passthrough"
)
preprocessor.fit(X_train)
X_train_processed = preprocessor.transform(X_train)
X_test_processed = preprocessor.transform(X_test)
# print(X_train_processed.shape)
# print(X_test_processed.shape)

from sklearn.pipeline import Pipeline

numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])
numerical_pipeline.fit(X_train[numerical_columns])

X_train_num = numerical_pipeline.transform(
    X_train[numerical_columns]
)

X_test_num = numerical_pipeline.transform(
    X_test[numerical_columns]
)
# print(X_train_num.shape)
# print(X_test_num.shape)

categorical_pipeline = Pipeline([
    ("encoder", OneHotEncoder(
        handle_unknown="ignore"
    ))
])
categorical_pipeline.fit(
    X_train[categorical_columns]
)

X_train_cat = categorical_pipeline.transform(
    X_train[categorical_columns]
)

X_test_cat = categorical_pipeline.transform(
    X_test[categorical_columns]
)
# print(X_train_cat.shape)
# print(X_test_cat.shape)

passthrough_columns = [
    "city_tier",
    "satisfaction_score",
    "complain"
]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numerical_pipeline, numerical_columns),
        ("cat", categorical_pipeline, categorical_columns)
    ],
    remainder="passthrough"
)
preprocessor.fit(X_train)

X_train_processed = preprocessor.transform(X_train)
X_test_processed = preprocessor.transform(X_test)
# print("X_train:", X_train_processed.shape)
# print("X_test :", X_test_processed.shape)

from sklearn.linear_model import LogisticRegression

model = LogisticRegression(max_iter=1000)
model_pipeline = Pipeline([ ("preprocessor", preprocessor), ("model", model)])

model_pipeline.fit(X_train, y_train)  ## model learns trainbing data 

y_pred = model_pipeline.predict(X_test)  ## model predicts the test data in 1/0

y_probability = model_pipeline.predict_proba(X_test)[:, 1]  ## model gives probability 

# print("Predictions:", y_pred[:10])
# print("Probabilities:", y_probability[:10])

from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_test, y_pred)
# print(cm)

from sklearn.metrics import ( accuracy_score, precision_score, recall_score, f1_score )

# print("Accuracy :", accuracy_score(y_test, y_pred)*100 ,"%" )
# print("Precision:", precision_score(y_test, y_pred)*100 ,"%" )
# print("Recall   :", recall_score(y_test, y_pred)*100 ,"%")
# print("F1 Score :", f1_score(y_test, y_pred)*100 ,"%")

from sklearn.metrics import roc_auc_score

roc_auc = roc_auc_score(y_test, y_probability)
# print("ROC-AUC:", roc_auc*100 ,"%")

from sklearn.metrics import average_precision_score

pr_auc = average_precision_score( y_test , y_probability)
# print("PR-AUC: " , pr_auc*100 ,"%")

# print(y_train.value_counts())
# print(y_train.value_counts(normalize=True).mul(100).round(2))

from sklearn.linear_model import LogisticRegression

balanced_model = LogisticRegression(
    class_weight="balanced",
    max_iter=1000
)
balanced_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", balanced_model)
])
balanced_pipeline.fit(X_train, y_train)
y_pred_balanced = balanced_pipeline.predict(X_test)
y_probability_balanced = balanced_pipeline.predict_proba(X_test)[:, 1]

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score )

# print("Accuracy :", accuracy_score(y_test, y_pred_balanced)*100 , "%")
# print("Precision:", precision_score(y_test, y_pred_balanced)*100 , "%")
# print("Recall   :", recall_score(y_test, y_pred_balanced)*100 , "%")
# print("F1 Score :", f1_score(y_test, y_pred_balanced)*100 , "%")
# print("ROC-AUC  :", roc_auc_score(y_test, y_probability_balanced)*100 , "%")
# print("PR-AUC   :", average_precision_score(y_test, y_probability_balanced)*100 , "%")

# print(confusion_matrix(y_test, y_pred_balanced))

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline

smote = SMOTE(random_state=42)
smote_model = LogisticRegression(max_iter=1000)
smote_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("smote", smote),
    ("model", smote_model)
])

smote_pipeline.fit(X_train, y_train)
y_pred_smote = smote_pipeline.predict(X_test)

y_probability_smote = (
    smote_pipeline.predict_proba(X_test)[:, 1]
)

# print("Accuracy :", accuracy_score(y_test, y_pred_smote)* 100 , "%")
# print("Precision:", precision_score(y_test, y_pred_smote)* 100 , "%")
# print("Recall   :", recall_score(y_test, y_pred_smote)* 100 , "%")
# print("F1 Score :", f1_score(y_test, y_pred_smote)* 100 , "%")
# print("ROC-AUC  :", roc_auc_score(y_test, y_probability_smote)* 100 , "%")
# print("PR-AUC   :", average_precision_score( y_test, y_probability_smote)* 100 , "%")

import numpy as np
thresholds = [0.50, 0.45, 0.40, 0.35, 0.30, 0.25]
for threshold in thresholds:

    y_pred_threshold = ( y_probability >= threshold ).astype(int)

    precision = precision_score( y_test, y_pred_threshold )

    recall = recall_score( y_test, y_pred_threshold )
    f1 = f1_score( y_test, y_pred_threshold )

    # print(
    #     f"Threshold: {threshold:.2f} | "
    #     f"Precision: {precision:.3f} | "
    #     f"Recall: {recall:.3f} | "
    #     f"F1: {f1:.3f}"
    # )


from sklearn.tree import DecisionTreeClassifier

dt_model = DecisionTreeClassifier( max_depth=5 , random_state=42)
dt_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", dt_model)
])

dt_pipeline.fit(X_train, y_train)

y_pred_dt = dt_pipeline.predict(X_test)


y_probability_dt = (
    dt_pipeline.predict_proba(X_test)[:, 1]
)

cm = confusion_matrix(y_test, y_pred_dt)
# print("\n\n",cm)

# print("Accuracy :", accuracy_score(y_test, y_pred_dt)*100 , "%")
# print("Precision:", precision_score(y_test, y_pred_dt)*100 , "%")
# print("Recall   :", recall_score(y_test, y_pred_dt)*100 , "%")
# print("F1 Score :", f1_score(y_test, y_pred_dt)*100 , "%")
# print("ROC-AUC  :", roc_auc_score(y_test, y_probability_dt)*100 , "%")
# print("PR-AUC   :", average_precision_score( y_test, y_probability_dt)*100 , "%")


from sklearn.ensemble import RandomForestClassifier

rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42
)
rf_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", rf_model)
])

rf_pipeline.fit(X_train, y_train)

y_pred_rf = rf_pipeline.predict(X_test)
y_probability_rf = (
    rf_pipeline.predict_proba(X_test)[:, 1]
)

cm = confusion_matrix(y_test, y_pred_rf)
# print("\n\n",cm)
# print("Accuracy :", accuracy_score(y_test, y_pred_rf)*100 , "%")
# print("Precision:", precision_score(y_test, y_pred_rf)*100 , "%")
# print("Recall   :", recall_score(y_test, y_pred_rf)*100 , "%")
# print("F1 Score :", f1_score(y_test, y_pred_rf)*100 , "%")
# print("ROC-AUC  :", roc_auc_score(y_test, y_probability_rf)*100 , "%")
# print("PR-AUC   :", average_precision_score( y_test, y_probability_rf)*100 , "%")

y_train_pred_rf = rf_pipeline.predict(X_train)
y_test_pred_rf = rf_pipeline.predict(X_test)
# print(
#     "Train Accuracy:",
#     accuracy_score(y_train, y_train_pred_rf)
# )

# print(
#     "Test Accuracy:",
#     accuracy_score(y_test, y_test_pred_rf)
# )
y_train_prob_rf = (
    rf_pipeline.predict_proba(X_train)[:, 1]
)

y_test_prob_rf = (
    rf_pipeline.predict_proba(X_test)[:, 1]
)
# print(
#     "Train ROC-AUC:",
#     roc_auc_score(y_train, y_train_prob_rf)
# )

# print(
#     "Test ROC-AUC:",
#     roc_auc_score(y_test, y_test_prob_rf)
# )

feature_names = (
    rf_pipeline.named_steps["preprocessor"].get_feature_names_out())

# print(feature_names)

importance = (
    rf_pipeline.named_steps["model"].feature_importances_)

feature_importance = pd.DataFrame({
    "feature": feature_names,
    "importance": importance
})
feature_importance = feature_importance.sort_values(
    "importance",
    ascending=False
)
# print("\n\n",feature_importance)


import shap
X_test_transformed = (
    rf_pipeline
    .named_steps["preprocessor"]
    .transform(X_test)
)
rf_model = rf_pipeline.named_steps["model"]

explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(
    X_test_transformed
)
# print(type(shap_values))
# print(len(shap_values))
# print(shap_values.shape)
shap_churn = shap_values[:, :, 1]
# print(shap_churn.shape)

shap_df = pd.DataFrame(
    shap_churn,
    columns=feature_names
)
# print(shap_df.head())

churn_indexes = X_test.index[
    y_test_pred_rf == 1
]

# print(churn_indexes[:5])
customer_index = churn_indexes[0]

# print(customer_index)
# print(X_test.loc[customer_index])

customer_position = X_test.index.get_loc(customer_index)

customer_shap = shap_df.iloc[customer_position]

# print( customer_shap.sort_values(ascending=False))

# shap.summary_plot(
#     shap_churn,
#     X_test_transformed,
#     feature_names=feature_names
# )


customer_probability = rf_pipeline.predict_proba(
    X_test.loc[[customer_index]] )[0, 1]

# print(
#     f"Churn Probability: {customer_probability:.2%}"
# )

positive_factors = (
    customer_shap[ customer_shap > 0 ].sort_values(ascending=False) )
# print(positive_factors.head(5))

negative_factors = (
    customer_shap[ customer_shap < 0 ].sort_values())
# print(negative_factors.head(5))

print("\n===== TOP CHURN RISK FACTORS =====")

for feature, value in positive_factors.head(5).items():
    print(f"{feature}: +{value:.4f}")

print("\n===== TOP PROTECTIVE FACTORS =====")

for feature, value in negative_factors.head(5).items():
    print(f"{feature}: {value:.4f}")


rf_balanced = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        class_weight="balanced",
        random_state=42
    ))
])

rf_balanced.fit(X_train, y_train)
y_pred_rf_balanced = rf_balanced.predict(X_test)
y_prob_rf_balanced  = rf_balanced.predict_proba(X_test)[:, 1]

print("\n\n",confusion_matrix(y_test, y_pred_rf_balanced)) 

print("Accuracy :", accuracy_score(y_test, y_pred_rf_balanced) * 100, "%")
print( "Precision:", precision_score(y_test, y_pred_rf_balanced) * 100, "%")
print( "Recall   :", recall_score(y_test, y_pred_rf_balanced) * 100, "%")
print( "F1 Score :", f1_score(y_test, y_pred_rf_balanced) * 100, "%")
print( "ROC-AUC  :", roc_auc_score(y_test, y_prob_rf_balanced) * 100, "%")
print("PR-AUC   :", average_precision_score(y_test, y_prob_rf_balanced) * 100, "%")


from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE

rf_smote = Pipeline([
    ("preprocessor", preprocessor),
    ("smote", SMOTE(random_state=42)),
    ("model", RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        random_state=42
    ))
])
rf_smote.fit(X_train, y_train)
y_pred_smote = rf_smote.predict(X_test)
y_prob_smote = rf_smote.predict_proba(X_test)[:, 1]

# print("\n\n",confusion_matrix(y_test, y_pred_smote)) 

# print("Accuracy :", accuracy_score(y_test, y_pred_smote) * 100, "%")
# print( "Precision:", precision_score(y_test, y_pred_smote) * 100, "%")
# print( "Recall   :", recall_score(y_test, y_pred_smote) * 100, "%")
# print( "F1 Score :", f1_score(y_test, y_pred_smote) * 100, "%")
# print( "ROC-AUC  :", roc_auc_score(y_test, y_prob_smote) * 100, "%")
# print("PR-AUC   :", average_precision_score(y_test, y_prob_smote) * 100, "%")

y_prob_balanced = rf_balanced.predict_proba(X_test)[:, 1]
for threshold in [0.50, 0.45, 0.40, 0.35, 0.30, 0.25]:

    y_pred_threshold = (y_prob_balanced >= threshold ).astype(int)

    precision = precision_score( y_test,y_pred_threshold )

    recall = recall_score(  y_test, y_pred_threshold )

    f1 = f1_score(  y_test, y_pred_threshold )

    # print(
    #     f"Threshold: {threshold:.2f} | "
    #     f"Precision: {precision:.3f} | "
    #     f"Recall: {recall:.3f} | "
    #     f"F1: {f1:.3f}"
    # )


from sklearn.model_selection import StratifiedKFold, cross_val_score
cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

cv_recall = cross_val_score(
    rf_balanced,
    X_train,
    y_train,
    cv=cv,
    scoring="recall"
)

print("Recall scores:", cv_recall)
print("Mean Recall:", cv_recall.mean())

cv_f1 = cross_val_score(
    rf_balanced,
    X_train,
    y_train,
    cv=cv,
    scoring="f1"
)

print("F1 scores:", cv_f1)
print("Mean F1:", cv_f1.mean())

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

rf_normal = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        random_state=42
    ))
])

rf_balanced = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        class_weight="balanced",
        random_state=42
    ))
])

rf_smote = ImbPipeline([
    ("preprocessor", preprocessor),
    ("smote", SMOTE(random_state=42)),
    ("model", RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        random_state=42
    ))
])

models = {
    "Normal RF": rf_normal,
    "Balanced RF": rf_balanced,
    "SMOTE RF": rf_smote
}

for name, model in models.items():

    recall = cross_val_score(
        model,
        X_train,
        y_train,
        cv=cv,
        scoring="recall"
    )

    f1 = cross_val_score(
        model,
        X_train,
        y_train,
        cv=cv,
        scoring="f1"
    )

    print(f"\n{name}")
    print(f"Mean Recall: {recall.mean():.3f}")
    print(f"Mean F1    : {f1.mean():.3f}")



