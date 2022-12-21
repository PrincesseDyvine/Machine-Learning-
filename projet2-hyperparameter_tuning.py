# -*- coding: utf-8 -*-
"""Copie de Chap 2.2: HyperParameter Tuning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ltulrwgowmsbnf0rQ6TD69tJbmBzxYpw

# Chapter 2 (Part 2):  Finetune your model

## Previously in Chapter 2:

### Import Libraries
"""

# Commented out IPython magic to ensure Python compatibility.
import os
import tarfile
from six.moves import urllib
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score
# %matplotlib inline
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer

"""### Loading Data """

#This is where the data are hosted
DOWNLOAD_ROOT = "https://raw.githubusercontent.com/ageron/handson-ml2/master/" 
HOUSING_URL = DOWNLOAD_ROOT + "datasets/housing/housing.tgz" #data path

#This is where we will store downloaded data
HOUSING_PATH = os.path.join("datasets", "housing")

def fetch_housing_data(housing_url=HOUSING_URL, housing_path=HOUSING_PATH):
  if not os.path.isdir(housing_path):
    os.makedirs(housing_path)
  tgz_path = os.path.join(housing_path, "housing.tgz")
  urllib.request.urlretrieve(housing_url, tgz_path)
  housing_tgz = tarfile.open(tgz_path)
  housing_tgz.extractall(path=housing_path)
  housing_tgz.close()

def load_housing_data(housing_path=HOUSING_PATH):
  csv_path = os.path.join(housing_path, "housing.csv")
  return pd.read_csv(csv_path)

#Download data
fetch_housing_data()
#load the data
housing = load_housing_data()
print(housing.head())

"""### Create a stratified train/test set"""

housing["income_cat"] = pd.cut(housing["median_income"],
                               bins=[0., 1.5, 3.0, 4.5, 6., np.inf],
                               labels=[1, 2, 3, 4, 5])

split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_index, test_index in split.split(housing, housing["income_cat"]):
 strat_train_set = housing.loc[train_index]
 strat_test_set = housing.loc[test_index]

for set_ in (strat_train_set, strat_test_set):
    set_.drop("income_cat", axis=1, inplace=True)

"""### Plot Train data"""

housing.plot(kind="scatter", x="longitude", y="latitude", alpha=0.4,
 s=housing["population"]/100, label="population", figsize=(10,7),
 c="median_house_value", cmap=plt.get_cmap("jet"), colorbar=True,
)

plt.legend()

"""### Train data and labels"""

housing = strat_train_set.drop("median_house_value", axis=1)
housing_labels = strat_train_set["median_house_value"].copy()

"""### Data preparation"""

col_names = "total_rooms", "total_bedrooms", "population", "households"
rooms_ix, bedrooms_ix, population_ix, households_ix = [
    housing.columns.get_loc(c) for c in col_names] # get the column indices

class CombinedAttributesAdder(BaseEstimator, TransformerMixin):
    def __init__(self, add_bedrooms_per_room=True): # no *args or **kargs
        self.add_bedrooms_per_room = add_bedrooms_per_room
    def fit(self, X, y=None):
        return self  # nothing else to do
    def transform(self, X):
        rooms_per_household = X[:, rooms_ix] / X[:, households_ix]
        population_per_household = X[:, population_ix] / X[:, households_ix]
        if self.add_bedrooms_per_room:
            bedrooms_per_room = X[:, bedrooms_ix] / X[:, rooms_ix]
            return np.c_[X, rooms_per_household, population_per_household,
                         bedrooms_per_room]
        else:
            return np.c_[X, rooms_per_household, population_per_household]

num_pipeline = Pipeline([
 ('imputer', SimpleImputer(strategy="median")),
 ('attribs_adder', CombinedAttributesAdder()),
 ('std_scaler', StandardScaler()),
 ])

housing_num = housing.drop("ocean_proximity", axis=1)
num_attribs = list(housing_num)
cat_attribs = ["ocean_proximity"]
full_pipeline = ColumnTransformer([
 ("num", num_pipeline, num_attribs),
 ("cat", OneHotEncoder(), cat_attribs),
 ])
housing_prepared = full_pipeline.fit_transform(housing)

"""### Train Linear Model"""

lin_reg = LinearRegression()
lin_reg.fit(housing_prepared, housing_labels)
housing_predictions = lin_reg.predict(housing_prepared)
lin_mse = mean_squared_error(housing_labels, housing_predictions)
lin_rmse = np.sqrt(lin_mse)
lin_rmse

"""Train Decision Tree Model"""

tree_reg = DecisionTreeRegressor(random_state=42)
tree_reg.fit(housing_prepared, housing_labels)
housing_predictions = tree_reg.predict(housing_prepared)
tree_mse = mean_squared_error(housing_labels, housing_predictions)
tree_rmse = np.sqrt(tree_mse)
tree_rmse

"""### Train Random Forest Model"""

forest_reg = RandomForestRegressor(n_estimators=100, random_state=42)
forest_reg.fit(housing_prepared, housing_labels)
housing_predictions = forest_reg.predict(housing_prepared)
forest_mse = mean_squared_error(housing_labels, housing_predictions)
forest_rmse = np.sqrt(forest_mse)
forest_rmse

"""### Use Cross Validation"""

def display_scores(scores):
  print("Scores:", scores)
  print("Mean:", scores.mean())
  print("Standard deviation:", scores.std())


lin_scores = cross_val_score(lin_reg, housing_prepared, housing_labels, scoring="neg_mean_squared_error", cv=10)
lin_rmse_scores = np.sqrt(-lin_scores)
display_scores(lin_rmse_scores)

scores = cross_val_score(tree_reg, housing_prepared, housing_labels,
 scoring="neg_mean_squared_error", cv=10)
tree_rmse_scores = np.sqrt(-scores)
display_scores(tree_rmse_scores)

forest_scores = cross_val_score(forest_reg, housing_prepared, housing_labels,
                                scoring="neg_mean_squared_error", cv=10)
forest_rmse_scores = np.sqrt(-forest_scores)
display_scores(forest_rmse_scores)

"""## Finetuning Hyper Parameters

Let’s assume that you now have a shortlist of promising models. You now need to
fine-tune them. Let’s look at a few ways you can do that.

One way to do that would be to fiddle with the hyperparameters manually, until you
find a great combination of hyperparameter values. This would be very tedious work,
and you may not have time to explore many combinations.

Instead you should get Scikit-Learn’s GridSearchCV to search for you. All you need to
do is tell it which hyperparameters you want it to experiment with, and what values to
try out, and it will evaluate all the possible combinations of hyperparameter values,
using cross-validation. For example, the following code searches for the best combination of hyperparameter values for the RandomForestRegressor:

```
class  sklearn.ensemble.RandomForestRegressor(
  n_estimators=100, 
  criterion='squared_error',
  max_depth=None, 
  min_samples_split=2, 
  min_samples_leaf=1, 
  min_weight_fraction_leaf=0.0, 
  max_features='auto', 
  max_leaf_nodes=None, 
  min_impurity_decrease=0.0, 
  bootstrap=True, 
  oob_score=False, 
  n_jobs=None, 
  random_state=None, 
  verbose=0, 
  warm_start=False, 
  ccp_alpha=0.0, 
  max_samples=None
)
```

Try to finetune the following hyper parameters using GridSearchCV:
- With bootstrap: 
  - n_estimators : 3,5,10,30
  - max_features : 1,2,4,8

- Without bootstrap: 
  - n_estimators : 3,10
  - max_features : 2,3,4
"""

from sklearn.model_selection import GridSearchCV
param_grid = [{'n_estimators':[3,5,10,30],'max_features': [1,2,4,8]},{'n_estimators': [3,10],'max_features': [2,3,4],'bootstrap':[False]}]
forest_reg = RandomForestRegressor()
grid_search =GridSearchCV(forest_reg,param_grid, cv=5) 

#Fit the grid search
grid_search.fit(housing_prepared,housing_labels)

"""Get best parameters"""

grid_search.best_params_

"""or get the best estimator directly"""

grid_search.best_estimator_

"""Check the evaluation scores of the GridSearch"""

cvres = grid_search.cv_results_
for mean_score, params in zip(cvres["mean_test_score"], cvres["params"]):
  print(np.sqrt(-mean_score), params)

"""The grid search approach is fine when you are exploring relatively few combinations,
like in the previous example, but when the hyperparameter search space is large, it is
often preferable to use RandomizedSearchCV instead. This class can be used in much
the same way as the GridSearchCV class, but instead of trying out all possible combinations, it evaluates a given number of random combinations by selecting a random
value for each hyperparameter at every iteration. This approach has two main benefits:
* If you let the randomized search run for, say, 1,000 iterations, this approach will
explore 1,000 different values for each hyperparameter (instead of just a few values per hyperparameter with the grid search approach).
* You have more control over the computing budget you want to allocate to hyper‐
parameter search, simply by setting the number of iterations.
"""

feature_importances = grid_search.best_estimator_.feature_importances_
extra_attribs = ["rooms_per_hhold", "pop_per_hhold", "bedrooms_per_room"]
cat_encoder = full_pipeline.named_transformers_["cat"]
cat_one_hot_attribs = list(cat_encoder.categories_[0])
attributes = num_attribs + extra_attribs + cat_one_hot_attribs

#show feat importance and their corresponding columns (sorted)
sorted(zip(feature_importances,attributes),reverse=True)

"""## Analyze the Best Models and Their Errors

You will often gain good insights on the problem by inspecting the best models. For
example, the RandomForestRegressor can indicate the relative importance of each
attribute for making accurate predictions:

Add new Transformer to select only best features
"""

def indices_of_top_k(arr, k):
    return np.sort(np.argpartition(np.array(arr), -k)[-k:])

class TopFeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, feature_importances, k):
        self.feature_importances = feature_importances
        self.k = k
    def fit(self, X, y=None):
        self.feature_indices_ =  indices_of_top_k(self.feature_importances, self.k)
        return self
    def transform(self, X):
        return  X[:, self.feature_indices_]

"""Append the new transformer to data preparation"""

preparation_and_feature_selection_pipeline = #create new pipeline !
housing_prepared_top_k_features = preparation_and_feature_selection_pipeline.fit_transform(housing)

"""Train the model and use RandomizedSearchCV for hyperparameter tuning"""

parameters = # define list of parameters for RandomizedSearchCV
forest_reg = RandomForestRegressor()
rand_search = # define RandomizedSearchCV for 10 iteration
rand_search.fit(housing_prepared_top_k_features, housing_labels)

"""## Evaluate Your System on the Test Set

After tweaking your models for a while, you eventually have a system that performs
sufficiently well. Now is the time to evaluate the final model on the test set. There is
nothing special about this process; just get the predictors and the labels from your
test set, run your full_pipeline to transform the data (call transform(), not
fit_transform(), you do not want to fit the test set!), and evaluate the final model
on the test set:
"""

final_model = grid_search.best_estimator_
#get the final rmse using test set !

final_rmse