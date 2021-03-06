import os
import re
import time
import numpy
import math

class Node(object):
    left = None
    right = None
    gain = None
    row = None
    id = None

def weighted_bagging(data,weights):
    #SELECTS N RANDOM WEIGHTED ITEMS OUT OF N ITEMS IN DATA WITH REPLACEMENT
    bag_indices = numpy.random.choice(len(data),len(data),p = weights)
    bag = []
    for i in bag_indices:
        bag.append(data[i])
    return bag

class DecisionTree:
    def __init__(self):
        self.name = ""
        self.data = []
        self.labels = set()

    def get_branches(self,data,c_id,row):
        # GETS LEFT AND RIGHT BRANCHES
        left = []
        right = []
        for temprow in data:
            if isinstance(row[c_id],float):
                if temprow[c_id] >= row[c_id]:
                    right.append(temprow)
                else:
                    left.append(temprow)
            elif isinstance(row[c_id],str):
                if temprow[c_id] == row[c_id]:
                    right.append(temprow)
                else:
                    left.append(temprow)

        return left, right

    def gini_index(self,rows):
        #CALCULATES GINI IMPURITY
        dict1 = {}

        for i in rows:
            if not dict1.__contains__(i[-1]):
                dict1[i[-1]] = 1.0
            else:
                dict1[i[-1]] += 1.0
        gini = 1.0
        for key in dict1.keys():
            gini = gini - (dict1[key]/len(rows))**2

        return gini




    def get_split(self,data):
        #GETS THE BEST SPLIT BY CALCULATING INFORMATION GAIN
        current_gini = self.gini_index(data) #Calculates impurity
        best_gain, best_row, best_c_id = 0, None, None
        if current_gini == 0:
            return best_gain, best_row, best_c_id
        for c_id in range(0,len(data[0])-1):
            for row in data:
                left, right = self.get_branches(data,c_id,row)
                if len(left) == 0 or len(right)== 0:
                    continue
                left_gini = self.gini_index(left)
                right_gini = self.gini_index(right)
                p_left = float(len(left))/len(data)
                p_right = 1.0 - p_left
                info_gain = current_gini - p_left*left_gini - p_right*right_gini

                if info_gain > best_gain:
                    best_row = row
                    best_c_id = c_id
                    best_gain = info_gain

        return best_gain, best_row, best_c_id

    def build_tree(self,data):
        #BUILDS TREE RECURSIVELY
        root = Node()
        gain, row, id = self.get_split(data)
        if row == None:
            row = data[0]
            root.gain = 0
            root.row = row
            return root

        root.gain = gain
        root.row = row
        root.id = id
        left, right = self.get_branches(data,id,row)
        root.left = self.build_tree(left)
        root.right = self.build_tree(right)
        return root

    def predict(self,node,row):
        #PREDICTS LABELS RECURSIVELY
        if node.right == None and node.left == None:
            return node.row[-1]
        if node.right == None or node.left == None:
            print ("Only one child created.")
        if isinstance(node.row[node.id], float):
            if row[node.id] >= node.row[node.id]:
                return self.predict(node.right,row)
            else:
                return self.predict(node.left,row)
        elif isinstance(node.row[node.id],str):
            if row[node.id] == node.row[node.id]:
                return self.predict(node.right,row)
            else:
                return self.predict(node.left,row)

#FINDS FILES
directory = os.path.normpath("input")
for subdir, dirs, files in os.walk(directory):
    for filename in files:
        if filename.endswith(".txt"):
            ob = DecisionTree()
            #READS DIMENSIONS
            start = time.time()
            num_rows = sum(1 for line in open("input/"+filename))
            with open("input/"+filename) as f:
                for i in f:
                    n = re.split(r'\t+', i)
                    ob.cols = len(n) - 2
                    break


            #READS DATA
            data = []
            labels = set()
            with open("input/"+filename) as f:
                for i in f:
                    row = []
                    n = re.split(r'\t+', i)
                    for j in range(0,len(n)):
                        try:
                            row.append(float(n[j]))
                        except ValueError:
                            row.append(n[j])
                    data.append(row)
                    labels.add(row[-1])

            #N - FOLD CROSS VALIDATION
            no_of_folds = 10
            batch = len(data) / no_of_folds
            print("\nRunning AdaBoost On "+filename)
            L = input("Please set the parameter L (number of classifiers):  ")
            sum1, sump, sumr, sumf = 0.0, 0.0, 0.0, 0.0
            for iteration in range(1,no_of_folds+1):
                count, a, b, c = 0.0, 0.0, 0.0, 0.0
                testing_data = []
                training_data = []
                for i, j in enumerate(data):
                    if (iteration == 1):
                        if (i >= 0 and i < int(iteration * batch)):
                            testing_data.append(j)
                        else:
                            training_data.append(j)
                    elif (iteration == no_of_folds):
                        if (i >= int((iteration - 1) * batch) and i <= len(data) - 1):
                            testing_data.append(j)
                        else:
                            training_data.append(j)
                    else:
                        if (i < int(batch * (iteration - 1)) or i >= int(iteration * batch)):
                            training_data.append(j)
                        else:
                            testing_data.append(j)
                ob = DecisionTree()
                C = []
                Alpha = []
                #INITIALIZE WEIGHTS
                w = numpy.ones(len(training_data))/len(training_data)
                #ITERATE L TIMES TO BUILD L TREES
                for i in range(int(L)):
                    bag = weighted_bagging(training_data,w)
                    rootNode = ob.build_tree(bag)
                    C.append(rootNode)
                    err = 0.0
                    negatively_classified = []
                    for j in range(len(training_data)):
                        if ob.predict(rootNode,training_data[j]) != training_data[j][-1]:
                            err += w[j]
                            negatively_classified.append(j)
                    alpha = 0.5*math.log((1.0-err)/err)
                    Alpha.append(alpha)
                    #UPDATE WEIGHTS
                    for j in range(len(training_data)):
                        if j in negatively_classified:
                            w[j] = w[j]*numpy.exp((-1*alpha)*-1)
                        else:
                            w[j] = w[j]*numpy.exp((-1*alpha))
                    w = w/numpy.sum(w)

                #TEST DATA
                for i in testing_data:
                    res = 0.0
                    for j in range(len(C)):
                        if ob.predict(C[j],i) == 1.0:
                            res += 1.0*Alpha[j]
                        else:
                            res += -1.0*Alpha[j]
                    if res >= 0:
                        label = 1.0
                    else:
                        label = 0.0

                    pred = label
                    if pred == i[-1]:
                        count += 1.0
                        if pred == 1.0:
                            a += 1.0
                    else:
                        if pred == 1.0:
                            c += 1.0
                        else:
                            b += 1.0

                print("Iteration" + str(iteration) + ": ")
                print("Accuracy: " + str(count / len(testing_data) * 100) + "%")
                print("Precision: " + str((a / (a + c)) * 100) + "%")
                print("Recall: " + str((a / (a + b)) * 100) + "%")
                print("F-measure: " + str(2 * a / (2 * a + b + c))+"\n")
                sum1 += count/len(testing_data)*100
                sump += (a / (a + c)) * 100
                sumr += (a / (a + b)) * 100
                sumf += 2 * a / (2 * a + b + c)
            end = time.time()

            #PRINT FINAL RESULTS
            print("Average Accuracy: "+str(sum1/no_of_folds)+"%")
            print("Average Precision: " + str(sump / no_of_folds) + "%")
            print("Average Recall: " + str(sumr / no_of_folds) + "%")
            print("Average F-measure: " + str(sumf / no_of_folds))
            print("Time Taken: "+str(end-start)+"s")