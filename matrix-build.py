"""
Script which imports tab-delimited text file containing mutation data from MSK-IMPACT
study, obtained by download from cBioportal. Text file was pre-processed by adding a column
listing the tumor type. The genelist consists of 87 genes. In the original file, genes not mutant
in a sample were indicated "NaN', and any alteration that was detected was explicitly described e.g. G12D.
To simplify, the input file identifies non-mutant genes in each sample as '0' and a mutation of any kind as '1'.
No effort has been made to exclude passenger mutations.
Approach: 5 classifiers are trained on 10,945 specimens, each with 87 genes that are either wild-type or mutant.
60 tumor types are included. User enters the list of genes mutated in unknown sample. Script then attempts to classify
unknown profile against each of the five classifiers. The report indicates the top candidate cancer type predicted by
each of the five classifiers. Then follows a table showing the probability estimated by each classifer that the unknown
sample represents each tumor type. This table is rank ordered by the average probability computed by each of the five
classifiers.
"""

# from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

import pandas as pd
from sklearn.metrics import classification_report
# from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.calibration import CalibratedClassifierCV

# read in the matrix of mutations/tissues as pandas dataframe
filematrix = "MSK-IMPACT-merged-binarized.txt"
data = pd.read_table(filematrix)

# X is the table of gene mutation calls (0,1) for each of the 87 genes.
# y is the true tissue type (n=60) for each specimen.
X = data.iloc[:, 2:]
y = data.iloc[:, 1]

# code below is for hard-coding the unknown specimen for testing
# unknown = data.iloc[8:9,2:]
# print unknown
# print type(unknown)
# print "Following sample selected as the UNKNOWN  for testing:"
# print data.iloc[8:9]

inputgenes = []
# inputgenes = ["APC", "KRAS"]
genes = list(data.columns.values)[2:]       # gets the list of genes from input file
print "Available Genes:", genes
input = raw_input("Enter comma-delimited list of reported mutant genes: ")
unformatted_input = list(input.split(","))

for e in unformatted_input:     # converts any entries to upper case, removes spaces etc.
    e = e.upper()
    e = e.strip()
    inputgenes.append(e)

for a in inputgenes:
    if a not in genes:
        print a, " not found."  # exits program if user enters a gene not in the list
        exit()


# build a dictionary from the input gene list in order to generate a pandas dataframe matching the input matrix order
unknowndict = {}
for i in genes:
    if i in inputgenes:
        unknowndict[i] = 1
    if i not in inputgenes:
        unknowndict[i] = 0
print unknowndict

unknownpdframe = pd.DataFrame.from_dict(unknowndict, orient='index')  # make dataframe from dict

unknownpdframe = unknownpdframe.sort_index(axis=0, ascending=True)  # sort dataframe to match test set
unknownpdframe = unknownpdframe.transpose()     # transpose dataframe to match test set
# print unknownpdframe

unknown = unknownpdframe

# Generate test and training sets.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=27)


# KNN model requires you to specify n_neighbors,
# the number of points the classifier will look at to determine what class a new point belongs to
KNN_model = KNeighborsClassifier(n_neighbors=5)
KNN_model.fit(X_train, y_train)
KNN_prediction = KNN_model.predict(X_test)

# Accuracy score is the simplest way to evaluate
print "accuracy score of KNN prediction:"
print accuracy_score(KNN_prediction, y_test)
# But Confusion Matrix and Classification Report give more details about performance
print "classification report KNN prediction (test set after building classifier with training set"
print classification_report(KNN_prediction, y_test)

# Create a dictionary called summary, in which to accumulate probability calls for each classifier
summary = {}

print "KNN prediction of identity of unknown"
KNN_top = KNN_model.predict(unknown)
print KNN_top
KNN_list = list(zip(KNN_model.classes_, KNN_model.predict_proba(unknown)[0]))
print KNN_list
# print (classification_report(answer, y_test))

for i in KNN_list:      # add probabilities to cumulative summary
    vals = []
    a, b = i
    vals.append(b)
    summary[a] = vals

print "Model: decision tree..."
clf = DecisionTreeClassifier()
clf.fit(X_train, y_train)
prob = clf.predict_proba(unknown)
dt_top = clf.predict(unknown)
print dt_top
print (prob)
dt_list = list(zip(clf.classes_, clf.predict_proba(unknown)[0]))
print "Decision tree results: ", dt_list

for i in dt_list:
    a, b = i
    for k, v in summary.items():     # adds the corresponding probability to cumulative summary
        if k == a:
            v.append(b)

# print "Cumulative summary:", summary

print "Model: skmultilearn"


clf = OneVsRestClassifier(DecisionTreeClassifier())
clf.fit(X_train, y_train)
prob = clf.predict_proba(unknown)
skmulti_top = clf.predict(unknown)
print skmulti_top
# print (prob)
skmulti_list = list(zip(clf.classes_, clf.predict_proba(unknown)[0]))
print skmulti_list

for i in skmulti_list:
    a, b = i
    for k, v in summary.items():     # adds the corresponding probability to cumulative summary
        if k == a:
            v.append(b)

print "Cumulative summary:", summary

logreg_clf = LogisticRegression()

logreg_clf.fit(X_train, y_train)
logreg_top = logreg_clf.predict(unknown)
prob = logreg_clf.predict_proba(unknown)
print "logistic regression"
print logreg_top
logreg_list = list(zip(logreg_clf.classes_, logreg_clf.predict_proba(unknown)[0]))
print logreg_list

for i in logreg_list:
    a, b = i
    for k, v in summary.items():     # adds the corresponding probability to cumulative summary
        if k == a:
            v.append(b)

print "SVM linear SVC"
svm = LinearSVC()
clf = CalibratedClassifierCV(svm)
clf.fit(X_train, y_train)
y_proba = clf.predict_proba(unknown)
SVM_Linear_top = clf.predict(unknown)

print SVM_Linear_top
SVM_Linear_list = list(zip(clf.classes_, clf.predict_proba(unknown)[0]))
print SVM_Linear_list

for i in SVM_Linear_list:
    a, b = i
    for k, v in summary.items():     # adds the corresponding probability to cumulative summary
        if k == a:
            v.append(b)


"""
# code below is if you need a thresholded report e.g. to report any cancer type in which at least one probability > 0.10
thresholded_summary = {}

for k,v in summary.items():
    for i in v:
        if i > 0.1:
            thresholded_summary[k] = v

print "Thresholded summary:", thresholded_summary
"""

average_probabilities = {}          # dictionary which will contain the average probability for each cancer type

for k, v in summary.items():
    average = 0

    for i in v:
        average = average + i
    average = average / len(v)
    average_probabilities[k] = average

# print average_probabilities
# output tuples is a list of tuples in which the first element is the tissue type and the second element is average probabilty
output_tuples = sorted(average_probabilities.items(), key=lambda x: x[1], reverse=True)

# print output_tuples

# for i in output_tuples:
#    print i

# Text report output
print "----------------------------------------------------------"
print "Mutant gene list: ", inputgenes
print "----------------------------------------------------------"
print "KNN top prediction: ", KNN_top
print "Decision Tree top prediction: ", dt_top
print "skmulti top prediction: ", skmulti_top
print "Logistic regression top prediction: ", logreg_top
print "Support Vector Machine Linear top prediction: ", SVM_Linear_top
print "----------------------------------------------------------"
print
print "Rank ordered list, by average probability: (KNN, Decision Tree, skmulti, Logistic regression, Support Vector Machine):"
print
for i in output_tuples:
    a, b = i
    for k, v in summary.items():
        if k == a:
            formatted_list = []         # list of probabilities for each specimen
            for n in v:
                formatted_list.append(round(n, 3))       # rounds the quoted probability to max of 3 decimal places

            print k, " "*(38-len(k)), formatted_list    # uses spaces to make column of numbers start at same point

print "----------------------------------------------------------"
