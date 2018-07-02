#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 15:45:06 2018

@author: zhangzhanming
"""

import plotly.offline as py
import plotly.graph_objs as go
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import itertools
import numpy as np
import pandas as pd
import Visualizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import scale
from sklearn.model_selection import cross_val_score
from sklearn import svm
#from sklearn.model_selection import cross_val_predict
from sklearn import metrics

class ModelAnalyzer(object):
    
    def __init__(self, model=None, raw_data=None, feature_data=None, prediction=None, 
                 target_data=None, class_data=None, target_class=None, class_mapping=None):
        self.model = model
        self.raw_data = raw_data
        self.feature_data = feature_data
        self.prediction = prediction
        self.target_data = target_data
        self.class_data = class_data
        self.class_mapping = class_mapping
        if target_class is not None and class_data is not None:
            target_data = class_data[target_class]
    

    def set_model(self, model):
        self.model = model
    

    def set_raw_data(self, raw_data):
        self.raw_data = raw_data
        

    def set_feature_data(self, feature_data):
        self.feature_data = feature_data
        

    def set_prediction(self, prediction):
        self.prediction = prediction


    def set_class_data(self, class_data):
        self.class_data = class_data


    def gen_confusion_matrix(self, prediction=None, 
                             target_data=None, normalize=True):
        if prediction is None:
            prediction = self.prediction
        if target_data is None:
            target_data = self.target_data
            
        class_names = target_data.unique().astype(str)
        cnf_matrix = confusion_matrix(target_data, prediction, labels=class_names)
        self.plot_confusion_matrix(cnf_matrix, class_names, normalize=normalize)

    
# =============================================================================
#     def train_model(self, feature_data=None, 
#                       target_data=None):
#         if feature_data is None:
#             feature_data = self.feature_data
#         if target_data is None:
#             target_data = self.target_data
#             
#         self.model.fit(feature_data, target_data)
#         return self.model
# 
# =============================================================================
    
    def get_confusion_data(self, time_series, true_value, predicted_value, target_data=None,
                           prediction=None, feature_data=None):
        if target_data is None:
            target_data = self.target_data
        if prediction is None:
            prediction= self.prediction
        if feature_data is None:
            feature_data = self.feature_data

        indexes = (target_data==true_value) & (prediction==predicted_value)
        times = time_series[indexes]
        features = feature_data.loc[indexes,:]
# =============================================================================
#         rawdata= pd.DataFrame(columns=self.raw_data.columns)
#         for index, series in times:
#             in_time = (self.raw_data.iloc[:,0] >= series[0]) & (self.raw_data.iloc[:,0] <= series[1])
#             pd.concat(rawdata, self.raw_data[in_time])
# =============================================================================
        
        return features

    def preprocess(in_data, classes, target_index, rescale=False):
        in_data.sort_values(by=['pid','START_TIME','STOP_TIME'], inplace=True)
        classes.sort_values(by=['pid','START_TIME','STOP_TIME'], inplace=True)
        in_data = in_data.reset_index().drop('index', axis=1)
        classes.reset_index(inplace=True)
        
        all((classes['START_TIME'] == in_data['START_TIME']) & (classes['pid'] == in_data['pid']))
        if len(in_data.columns) == 21:
            features = in_data.iloc[:,2:18]
        elif len(in_data.columns) == 39:
            features = in_data.iloc[:,list(range(2,18))+list(range(21,37))]
        if isinstance(target_index, str):
            target = classes[target_index]
        else:
            target = classes[classes.columns[target_index]]
        
        drop_list = (target == 'transition') | (target == 'unknown')
        target = target[~ drop_list]
        features = features[~ drop_list]
        if rescale: 
            features = scale(features)
        
        return features, target


    def plot_confusion_matrix(self, cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
        """
        This function prints and plots the confusion matrix.
        Normalization can be applied by setting `normalize=True`.
        """
        if normalize:
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            print("Normalized confusion matrix")
        else:
            print('Confusion matrix, without normalization')
    
        print(cm)
    
        plt.imshow(cm, interpolation='nearest', cmap=cmap)
        plt.title(title)
        plt.colorbar()
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)
    
        fmt = '.2f' if normalize else 'd'
        thresh = cm.max() / 2.
        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
            plt.text(j, i, format(cm[i, j], fmt),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
    
        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')


    def predict_with_real_data(self, time_stamps, real_features=None, class_mapping=None, real_annotation=None, target_class=None, model=None):
        if real_features is None: 
            real_features = self.feature_data
        if class_mapping is None:
            class_mapping = self.class_mapping
        if real_annotation is None:
            real_annotation = self.real_annotation
        if target_class is None:
            target_class = self.target_class
        if model is None:
            model = self.model
        
        real_features = real_features.dropna()
        prediction = model.predict(real_features)
        
        real_features['Result'] = prediction
        prediction_with_time = real_features.join(time_stamps.iloc[:,0:2])
        prediction_with_time = prediction_with_time.iloc[:,16:19]
        
        real_annotation = pd.merge(real_annotation, class_mapping, left_on ='LABEL_NAME', right_on='label', copy=False).drop('LABEL_NAME', axis=1)
        
        truth= []
        starttimelist = real_annotation['START_TIME']
        stoptimelist = real_annotation['STOP_TIME']
        
        for key, series in prediction_with_time.iterrows():
            starttime = series['START_TIME']
            stoptime = series['STOP_TIME']
            for i in range(len(starttimelist)+1):
                if i == len(starttimelist):
                    truth.append('not started')
                elif starttimelist[i] <= starttime:
                    if stoptimelist[i] >= stoptime:
                        truth.append(real_annotation.loc[real_annotation.index[i],target_class])
                        break
        
        truth = np.asarray(truth)   
        
        prediction_with_time['Truth'] = truth
            
        prediction_with_time = prediction_with_time.loc[~(prediction_with_time['Truth']=='not started'),:]    
        prediction_with_time = prediction_with_time.loc[~(prediction_with_time['Truth']=='nonwear'),:]    
        prediction_with_time = prediction_with_time.loc[~(prediction_with_time['Truth']=='unknown'),:]   
        self.target_data = prediction_with_time['Truth']
        self.prediction = prediction_with_time['Result']
        self.feature_data = real_features.loc[prediction_with_time.index,:]
        
        return prediction_with_time['Truth'],  prediction_with_time['Result']

    
    
    
test= False
if test:
    classes = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SampleData/spadeslab/SPADESInLab-cleaned.class.csv')
    in_data = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SampleData/DomAnkle.csv')
    in_data.drop(in_data.columns[0], axis =1, inplace=True)
    features, target = ModelAnalyzer.preprocess(in_data, classes, 'posture', False)
    model = RandomForestClassifier(n_estimators=50, n_jobs=-1)
    analyzer = ModelAnalyzer(model = model)
    analyzer.train_model(feature_data=features, target_data=target)
    aiden_feature_data = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/MyData/AIDEN.ANKLE.2018-06-20/Aiden/Derived/PostureAndActivity.feature.csv')
    
    analyzer.set_class_data()

        
        
        









        
        
        