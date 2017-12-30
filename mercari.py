
# coding: utf-8

# In[*]

import numpy as np
import pandas as pd
from time import time


# In[*]

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.utils.extmath import density
from sklearn import metrics
from sklearn.externals import joblib
from sklearn.model_selection import cross_val_predict
from sklearn import linear_model
import matplotlib.pyplot as plt
import math
get_ipython().magic('matplotlib inline')


# In[*]

train_df = pd.read_csv('data/mercari/train.tsv', sep='\t')
test_df = pd.read_csv('data/mercari/test.tsv', sep='\t')


# In[*]

train_df.describe()


# In[*]

train_df.shape


# In[*]

train_df.head()


# In[*]

print('Train columns with null values:\n', train_df.isnull().sum())
print("-"*10)

print('Test/Validation columns with null values:\n', test_df.isnull().sum())
print("-"*10)

train_df.describe(include = 'all')


# Calculate how much of the brand names are not there.

# In[*]

print(632682/train_df.shape[0])


# Around 50% is not there hence we should probably not consider this.

# In[*]

train_df = train_df.drop(['brand_name'], axis=1)
test_df = test_df.drop(['brand_name'], axis=1)


# # categories

# We need to check how many categories there are

# In[*]

# Merge the two dataframes
frames = [train_df, test_df]
combined_df = pd.concat(frames)


# In[*]

combined_cat_df = combined_df['category_name']
def split_cat(text):
    try: return text.split("/")
    except: pass

combined_cat_df = combined_cat_df.apply(lambda x: split_cat(x))


# In[*]

def no_of_cats(cat_list):
    try: return len(cat_list)
    except: return 0
    
no_of_cats = pd.DataFrame(combined_cat_df.apply(lambda x: no_of_cats(x)))


# In[*]

# no_of_cats['category_name'].max(axis=1)
index_whr_max_categories = no_of_cats['category_name'].argmax()
print(index_whr_max_categories)
max_num_of_categories = len(split_cat(combined_df.iloc[[index_whr_max_categories]]['category_name'].tolist()[0]))
print('there are a maximum of {} categories and this is happened in row:'.format(max_num_of_categories))
combined_df.iloc[[index_whr_max_categories]]


# In[*]

def split_cat(text, max_num_of_categories):
    return_val = ["None"] * max_num_of_categories
    try:
        text_list = text.split("/") + return_val
        return text_list[:max_num_of_categories]
    except:
        return return_val


# Change the category name for train and test and total dataframes

# In[*]

train_df['category_name'] = train_df['category_name'].apply(lambda x: split_cat(x, max_num_of_categories))
test_df['category_name'] = test_df['category_name'].apply(lambda x: split_cat(x, max_num_of_categories))
combined_df['category_name'] = combined_df['category_name'].apply(lambda x: split_cat(x, max_num_of_categories))


# In[*]

train_df.head()


# now we know that there are 5 categories so we will try to find the unknown ones category per category. so we will make predictions based on the 5 categories

# ### Running category encoding on the first category

# In[*]

combined_cat1_list = [x[0] for x in combined_df['category_name'].tolist()]
combined_cat1_list = [x for x in combined_cat1_list if not x == 'None']


# In[*]

cat1_le = LabelEncoder()
cat1_le.fit(combined_cat1_list)


# In[*]

cat1_le.transform(['Men', 'Electronics', 'Women', 'Home', 'Women'])


# In[*]

cat1_le.inverse_transform([5, 1, 9, 3, 9])


# Thus we are able to build a label encoder state space for the first category

# In[*]

def convert_catname_cat1(le, catlist):
    try:
        return le.transform(catlist[:1])[0]
    except:
        return np.nan


# In[*]

print('transform category name to first category as defined by the label encoding space for training set')
train_df['category_name'] = train_df['category_name'].apply(lambda x: convert_catname_cat1(cat1_le, x))
train_df.head()


# In[*]

print('transform category name to first category as defined by the label encoding space for test set')
test_df['category_name'] = test_df['category_name'].apply(lambda x: convert_catname_cat1(cat1_le, x))
test_df.head()


# There are some null values in item description so will need to make fill them.

# In[*]

print('presently number of null values in train and test.')
print(train_df['item_description'].isnull().sum())
print(test_df['item_description'].isnull().sum())


# In[*]

train_df['item_description'] = train_df['item_description'].fillna("")
test_df['item_description'] = test_df['item_description'].fillna("")
print('Num of null values in item description is for training set is {}.'.format(train_df['item_description'].isnull().sum()))
print('Num of null values in item description is for test set is {}.'.format(test_df['item_description'].isnull().sum()))
print('Ideally this number should be 0.')


# In[*]

train_df[train_df.isnull().any(axis=1)].head()


# In[*]

test_df[test_df.isnull().any(axis=1)].head()


# In[*]

value_list = ['iPhone']
train_df[train_df.name.isin(value_list)]


# For the missing category names we should try to find some unsupervised learning so that some amount filling of the data should be present.

# # Running NLP on the categories

# We will first try to classify the documents and see if we can get some meaningful classification based on that.

# Idea is to use only the name to predict the category name

# So we will drop all the remaining columns

# In[*]

print(train_df.columns.tolist())


# In[*]

from copy import deepcopy
category_df = deepcopy(train_df)


# In[*]

category_df = category_df.drop(['train_id', 'item_condition_id', 'price', 'shipping'], axis=1)


# In[*]

category_df.sample(2)


# In[*]

predict_category_df = category_df[pd.isnull(category_df['category_name'])]
train_test_categry_df = category_df[pd.notnull(category_df['category_name'])]
train_categry_df, test_categry_df = train_test_split(train_test_categry_df, test_size=0.2, random_state=42)
print('separated into predict, train and test')
print(category_df.shape, predict_category_df.shape, train_categry_df.shape, test_categry_df.shape)
print(predict_category_df.shape[0] + train_categry_df.shape[0] + test_categry_df.shape[0])


# In[*]

predict_category_df.head()


# In[*]

X_train_category_df = train_categry_df[['name', 'item_description']]
y_train_category_df = train_categry_df[['category_name']]
X_test_category_df = test_categry_df[['name', 'item_description']]
y_test_category_df = test_categry_df[['category_name']]
print('separate to x and y')
print(X_train_category_df.shape, y_train_category_df.shape, X_test_category_df.shape, y_test_category_df.shape)


# In[*]

y_train_category_df.head()


# In[*]

y_test_category_df.head()


# Combine the name and item_description

# In[*]

X_train_category_df.head()


# In[*]

X_train_category_df['total_text'] = X_train_category_df['name'] + " " +  X_train_category_df['item_description']
X_train_category_df.head()


# In[*]

X_test_category_df['total_text'] = X_test_category_df['name'] + " " +  X_test_category_df['item_description']
X_test_category_df.head()


# In[*]

print('Extracting features from the training data using a sparse vectorizer')
t0 = time()
vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5, stop_words='english')
x_train = vectorizer.fit_transform(X_train_category_df['total_text'])
duration = time() - t0
print("done in %fs" % (duration))    
print("n_samples: %d, n_features: %d" % x_train.shape)
print()


# In[*]

print('Extracting features from the testing data using a sparse vectorizer')
t0 = time()
x_test = vectorizer.transform(X_test_category_df['total_text'])
duration = time() - t0
print("done in %fs" % (duration))    
print("n_samples: %d, n_features: %d" % x_train.shape)
print()


# In[*]

feature_names = vectorizer.get_feature_names()


# In[*]

# #############################################################################  
# Benchmark classifiers                                                          
def fit_and_benchmark(clf, X_train, y_train, X_test, y_test, target_names):                                                              
    print('_' * 80)
    print("Training: ")
    print(clf)
    t0 = time()
    clf.fit(X_train, y_train)
    train_time = time() - t0
    print("train time: %0.3fs" % train_time)

    t0 = time()
    pred = clf.predict(X_test)
    test_time = time() - t0
    print("test time:  %0.3fs" % test_time)

    score = metrics.accuracy_score(y_test, pred)
    print("accuracy:   %0.3f" % score)
                                                                                 
    if hasattr(clf, 'coef_'):                                                    
        print("dimensionality: %d" % clf.coef_.shape[1])
        print("density: %f" % density(clf.coef_))
                                                                                 
        if feature_names is not None:                       
            print("top 10 keywords per class:")                                  
            for i, label in enumerate(target_names):                             
                top10 = np.argsort(clf.coef_[i])[-10:]
        print()
                                                                                 
    print("classification report:")
    print(metrics.classification_report(y_test, pred, target_names=target_names))          
                                                                                 
    print("confusion matrix:")
    print(metrics.confusion_matrix(y_test, pred))                            
                                                                                 
    print()                                                                      
    clf_descr = str(clf).split('(')[0]                                           
    print(clf_descr, score, train_time, test_time)
    return clf


# In[*]

# clf = VotingClassifier(estimators=[
#     ('rc', RidgeClassifier(tol=1e-2)),
#     ('perc', Perceptron(n_iter=50)),
#     ('pa', PassiveAggressiveClassifier(n_iter=50)),
#     ('knn', KNeighborsClassifier(n_neighbors=len(cat1_le.classes_))),
#     ('rfc', RandomForestClassifier(n_estimators=100)),
#     ('sgd', SGDClassifier(alpha=.0001, n_iter=50, penalty="elasticnet")),
#     ('SVC_with_L1', Pipeline([
#         ('feature_selection', SelectFromModel(LinearSVC(penalty="l1", dual=False, tol=1e-3))),
#         ('classification', LinearSVC(penalty="l2"))]))
# ])
# clf = VotingClassifier(estimators=[
#     ('rc', RidgeClassifier(tol=1e-2)),
#     ('perc', Perceptron(n_iter=50)),
#     ('pa', PassiveAggressiveClassifier(n_iter=50))
# ])
clf = VotingClassifier(estimators=[
    ('rc', RidgeClassifier(tol=1e-2))
])


# In[*]

clf = fit_and_benchmark(clf, x_train, y_train_category_df, x_test, y_test_category_df, cat1_le.classes_)


# ### fill the category name for the missing values and build the matrix

# In[*]

train_df['total_text'] = train_df['name'] + " " +  train_df['item_description']
train_df.head()


# In[*]

test_df['total_text'] = test_df['name'] + " " +  test_df['item_description']
test_df.head()


# In[*]

train_df_with_no_cat = train_df[train_df['category_name'].isnull()]
train_df_with_no_cat.head()


# In[*]

test_df_with_no_cat = test_df[test_df['category_name'].isnull()]
test_df_with_no_cat.head()


# In[*]

def fill_and_transform_df(df):
    new_df = deepcopy(df)
    for index, row in df.iterrows():
        if pd.isnull(row['category_name']):
            new_df.loc[index]['category_name'] = vectorizer.transform([row['total_text']])
        else:
            new_df.loc[index]['category_name'] = row['category_name']
    return new_df


# In[*]

matrix_train_df = vectorizer.transform(train_df_with_no_cat['total_text'])
pred_train_df = clf.predict(matrix_train_df)
print(pred_train_df.shape, train_df_with_no_cat.shape)


# In[*]

matrix_test_df = vectorizer.transform(test_df_with_no_cat['total_text'])
pred_test_df = clf.predict(matrix_test_df)
print(pred_test_df.shape, test_df_with_no_cat.shape)


# fill the category_names with the predicted values wherever they are not present. This will be used in further predictions using pytorch.

# In[*]

print(train_df.loc[122])
i = 0
for index, row in train_df_with_no_cat.iterrows():
    train_df.loc[train_df.train_id == index, ['category_name']] = pred_train_df[i]
    i += 1
print(train_df.loc[122])


# In[*]

i = 0
for index, row in test_df_with_no_cat.iterrows():
    test_df.loc[test_df.test_id == index, ['category_name']] = pred_test_df[i]
    i += 1


# In[*]

train_df[train_df['category_name'].isnull()]


# In[*]

train_df.head()


# In[*]

fig, ax = plt.subplots(1, 1, figsize=(11, 7), sharex=True)
sns.distplot(np.log(train_df['price'].values+1))


# In[*]

# vectorized error calc
def rmsle(y, y0):
    assert len(y) == len(y0)
    return np.sqrt(np.mean(np.power(np.log1p(y)-np.log1p(y0), 2)))
# Source: https://www.kaggle.com/jpopham91/rmlse-vectorized


# In[*]

print('lets see if there are some null values')
train_df.isnull().sum()


# In[*]

#PROCESS CATEGORICAL DATA
#print("Handling categorical variables...")
def encode_text(column):
    le = LabelEncoder()
    le.fit(np.hstack([train_df[column], test_df[column]]))
    train_df[column+'_index'] = le.transform(train_df[column])
    test_df[column+'_index'] = le.transform(test_df[column])


# In[*]

train_df.columns.to_series().groupby(train_df.dtypes).groups


# In[*]

train_df.select_dtypes(exclude=['float64', 'int64']).head()


# In[*]

train_df.head()


# In[*]

print('since brand name is not included now so the below code is not really required but keeping it for future consideration')
# encode_text('brand_name')


# In[*]

test_df.head()


# In[*]

class Category:
    def __init__(self, name):
        self.name = name
        self.word2index = {}
        self.word2count = {}
        self.index2word = {0: "SOS", 1: "EOS"}
        self.n_words = 2  # Count SOS and EOS

    def addSentence(self, sentence):
        for word in sentence.split(' '):
            self.addWord(word)

    def addWord(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.n_words
            self.word2count[word] = 1
            self.index2word[self.n_words] = word
            self.n_words += 1
        else:
            self.word2count[word] += 1


# In[*]

# Turn a Unicode string to plain ASCII, thanks to
# http://stackoverflow.com/a/518232/2809427
import unicodedata
import re
def unicodeToAscii(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# Lowercase, trim, and remove non-letter characters


def normalizeString(s):
    #s = unicodeToAscii(s.lower().strip())
    s = re.sub(r"([.!?])", r" \1", s)
    s = re.sub(r"[^a-zA-Z.!?]+", r" ", s)
    return s

def normalizeLine(sentence):
    return [normalizeString(s) for s in sentence.split('\t')]


# In[*]

def prepareData(lang1,data):
    input_cat = Category(lang1)
    for sentence in data:
        normalize_line = [normalizeString(s) for s in sentence.split('\t')]
        input_cat.addSentence(normalize_line[0])
        
    print("Counted words:")
    print(input_cat.name, input_cat.n_words)
    return input_cat


# In[*]

def indexesFromSentence(lang, sentence):
    return [lang.word2index[word] for word in sentence.split(' ')]

def variableFromSentence(lang, sentence):
    indexes = indexesFromSentence(lang, sentence)
    #indexes.append(EOS_token)
    return indexes


# In[*]

def token_fit(column):
    raw_text = np.hstack([(train_df[column]).str.lower(), (test_df[column]).str.lower()])
    cat1 = prepareData(column,raw_text)
    print ("adding train data")
    train_df[column + '_seq'] = [variableFromSentence(cat1,normalizeLine(sentence.lower())[0]) for sentence in train_df[column]]
    print ("adding test data")
    test_df[column + '_seq'] = [variableFromSentence(cat1,normalizeLine(sentence.lower())[0]) for sentence in test_df[column]]


# In[*]

token_fit('name')


# In[*]

token_fit('item_description')


# In[*]

train_df.head()


# In[*]

# # save the csvs
# train_df.to_csv('data/mercari/train.1.csv')
# test_df.to_csv('data/mercari/test.1.csv')
# print('transformed train and test data saved.')


# In[*]

# # save the classifiers
# from sklearn.externals import joblib
# joblib.dump(clf, 'data/mercari/clf.pkl')
# print('model is saved')


# In[*]

# load the csv and the model
clf = joblib.load('data/mercari/clf.pkl')
train_df = pd.read_csv('data/mercari/train.1.csv')
test_df = pd.read_csv('data/mercari/test.1.csv')


# In[*]

# this is needed because the dtypes of name_seq and item_description_seq is wrong
import ast
train_df['name_seq'] = train_df['name_seq'].apply(ast.literal_eval)
train_df['item_description_seq'] = train_df['item_description_seq'].apply(ast.literal_eval)
test_df['name_seq'] = test_df['name_seq'].apply(ast.literal_eval)
test_df['item_description_seq'] = test_df['item_description_seq'].apply(ast.literal_eval)


# In[*]

train_df['name_seq'] = train_df['name_seq'].apply(lambda x: np.array(x))
train_df['item_description_seq'] = train_df['item_description_seq'].apply(lambda x: np.array(x))
test_df['name_seq'] = test_df['name_seq'].apply(lambda x: np.array(x))
test_df['item_description_seq'] = test_df['item_description_seq'].apply(lambda x: np.array(x))


# In[*]

train_df_total_text_matrix = vectorizer.transform(train_df['total_text'])
test_df_total_text_matrix = vectorizer.transform(test_df['total_text'])


# In[*]

x_train = train_df[['item_condition_id', 'category_name', 'shipping']]
y_train = train_df['price']


# In[*]

x_train.as_matrix().shape, train_df_total_text_matrix.shape


# In[*]

train_df_total_text_matrix.T.shape


# In[*]

a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6, 1], [3,4, 1]])


# In[*]

a.shape, b.shape


# In[*]

np.concatenate((a, b), axis=1)


# In[*]

# np.concatenate((x_train.as_matrix(), train_df_total_text_matrix), axis=1)


#  ## Make a matrix out of the whole thing

# In[*]

x_train_1 = train_df[['item_condition_id', 'category_name', 'shipping']]
y_train_1 = train_df['price']
x_test_1 = test_df[['item_condition_id', 'category_name', 'shipping']]


# In[*]

x_test_1.head()


# In[*]

#EXTRACT DEVELOPTMENT TEST
X_dtrain, X_dvalid, y_dtrain, y_dvalid = train_test_split(x_train_1, y_train_1, random_state=123, test_size=0.05)
print(X_dtrain.shape, X_dvalid.shape)
print(y_dtrain.shape, y_dvalid.shape)


# In[*]

# #EXTRACT DEVELOPTMENT TEST
# dtrain, dvalid = train_test_split(train_df, random_state=123, train_size=0.99)
# print(dtrain.shape)
# print(dvalid.shape)


# In[*]

# x_dtrain = dtrain[['item_condition_id', 'category_name', 'shipping', 'name_seq', 'item_description_seq']]
# y_dtrain = dtrain['price']
# x_dval = dvalid[['item_condition_id', 'category_name', 'shipping', 'name_seq', 'item_description_seq']]
# y_dval = dvalid['price']


# In[*]

# Function to calculate the RMSLE on the validation data
def rmsle(y, y_pred):
    assert len(y) == len(y_pred)
    to_sum = [(math.log(y_pred[i] + 1) - math.log(y[i] + 1)) ** 2.0 for i,pred in enumerate(y_pred)]
    return (sum(to_sum) * (1.0/len(y))) ** 0.5


# In[*]

# y_dtrain.as_matrix().shape


# In[*]

from sklearn import linear_model
reg = linear_model.Ridge(alpha = .5)
reg.fit(X_dtrain, y_dtrain) 


# In[*]

predicted = reg.predict(X_dvalid)
predicted.shape


# In[*]

y_dvalid.shape


# In[*]

print('the score got from a simple ridge regression is:')
print(rmsle(y_dvalid.as_matrix(), predicted))


# In[*]

from sklearn.metrics import mean_squared_error
print(mean_squared_error(y_dvalid.as_matrix(), predicted))


# ## Ordinary Least Squares

# In[*]

import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score

# Create linear regression object
regr = linear_model.LinearRegression()

# Train the model using the training sets
regr.fit(X_dtrain, y_dtrain)

# Make predictions using the testing set
y_pred = regr.predict(X_dvalid)

# The coefficients
print('Coefficients: \n', regr.coef_)
# The mean squared error
print("Mean squared error: %.2f"
      % mean_squared_error(y_dvalid, y_pred))
# Explained variance score: 1 is perfect prediction
print('Variance score: %.2f' % r2_score(y_dvalid, y_pred))

# Plot outputs
plt.scatter(list(X_dvalid.index), y_dvalid,  color='black')
plt.plot(list(X_dvalid.index), y_pred, color='blue', linewidth=3)

plt.xticks(())
plt.yticks(())

plt.show()


# References:
# 
# https://www.kaggle.com/kswamy15/mercari-using-pytorch
# 
# http://scikit-learn.org/stable/modules/ensemble.html

# In[*]

axes = plt.gca()
axes.set_ylim([0,100])
plt.scatter(predicted,y_dvalid)


# In[*]

### Implement and save submission
x_test_1['price'] = reg.predict(x_test_1)
x_test_1['test_id'] = test_df['test_id']

print('Validation Data Distribution: \n', x_test_1['price'].value_counts(normalize = True))
submit.sample(10)


# In[*]

#submit file
submit = x_test_1[['test_id','price']]
submit.to_csv("data/mercari/sample_submission.csv", index=False)


# References:
# 
# https://www.kaggle.com/kswamy15/mercari-using-pytorch
# 
# http://scikit-learn.org/stable/modules/ensemble.html