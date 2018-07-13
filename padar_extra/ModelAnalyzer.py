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
import os 
import re
import plotly.offline as py
import plotly.figure_factory as ff
import InterativeHistogram


class ModelAnalyzer(object):
    
    def __init__(self, model=None, raw_data=None, feature_data=None, prediction=None, 
                 target_data=None, class_data=None, target_class=None, class_mapping=None,
                 real_annotation=None, root=None, aligned_features=None):
        self.model = model
        self.raw_data = raw_data
        self.feature_data = feature_data
        self.prediction = prediction
        self.target_data = target_data
        self.class_data = class_data
        self.class_mapping = class_mapping
        self.real_annotation=real_annotation
        self.target_class=target_class
        self.root = root
        self.aligned_features = aligned_features
        if target_class is not None and class_data is not None:
            self.target_data = class_data[target_class]
    

    def set_model(self, model):
        self.model = model
    

    def set_raw_data(self, raw_data):
        self.raw_data = raw_data
        

    def set_feature_data(self, feature_data):
        self.feature_data = feature_data
        
    def set_aligned_features(self, aligned_features):
        self.aligned_features = aligned_features

    def set_prediction(self, prediction):
        self.prediction = prediction


    def set_class_data(self, class_data):
        self.class_data = class_data

    def set_class_mapping(self, class_mapping):
        self.class_mapping = class_mapping
        
    def set_real_annotation(self, real_annotation):
        self.real_annotation = real_annotation

    def set_root(self, root):
        self.root = root 
    
    def gen_confusion_matrix(self, prediction=None, 
                             target_data=None, normalize=True):
        if prediction is None:
            prediction = self.prediction
        if target_data is None:
            target_data = self.target_data
            
        class_names = target_data.unique().astype(str)
        cnf_matrix = confusion_matrix(target_data, prediction, labels=class_names)
        self.plot_confusion_matrix(cnf_matrix, class_names, normalize=normalize)

    
    def get_confusion_data(self,true_value, predicted_value, target_data=None,
                           prediction=None, feature_data=None, root=None, 
                           get_feature_data=True, get_acc_data=True):
        if target_data is None:
            target_data = self.target_data
        if prediction is None:
            prediction= self.prediction
        if feature_data is None:
            feature_data = self.feature_data
        if root is None:
            root = self.root

        if get_feature_data:
            indexes = (target_data==true_value) & (prediction==predicted_value)
            features = feature_data.loc[indexes,:]  
            if not get_acc_data:
                return features
            
        if get_acc_data:
            times = feature_data.loc[indexes, ['START_TIME','STOP_TIME']]
            times.iloc[:,0] = pd.to_datetime(times.iloc[:,0])
            times.iloc[:,1] = pd.to_datetime(times.iloc[:,1])
            times['key'] = times['START_TIME'].dt.strftime('%Y/%m/%d/%H')
            
            grouped_time = times.groupby('key')
            acc_data = pd.DataFrame(columns=['HEADER_TIME_STAMP', 'X_ACCELERATION_METERS_PER_SECOND_SQUARED',
           'Y_ACCELERATION_METERS_PER_SECOND_SQUARED',
           'Z_ACCELERATION_METERS_PER_SECOND_SQUARED'])
            
            for key, data in grouped_time:
                file_list = []
                path = root+'MasterSynced/'+key
                for filename in os.listdir(path):
                    if re.findall(".sensor.csv", filename):
                        file_list.append(pd.read_csv(os.path.join(path, filename)))
                
                if len(file_list) > 1 or len(file_list) < 1:
                    raise Exception("Can't handle now: {} files found".format(len(file_list)))
                
                temp_acc = file_list[0]
                temp_acc.iloc[:,0] = pd.to_datetime(temp_acc.iloc[:,0])
                for i in range(data.shape[0]):
                    acc_data = acc_data.append(temp_acc[(temp_acc.iloc[:,0] >= data.iloc[i,0]) & 
                                                        (temp_acc.iloc[:,0] <= data.iloc[i,1])])
    
            if not get_feature_data:
                return acc_data
    
        return features, acc_data
    
    
    @staticmethod
    def plot_feature_and_raw(features, acc_data, path_out='/Users/zhangzhanming/Desktop/mHealth/Test/'):
        acc_fig = Visualizer.acc_grapher(acc_data, return_fig=True, showlegend=True)
        feature_fig = Visualizer.feature_grapher(features, return_fig=True, showlegend=True, hide_traces=True)
        acc_fig['data'] += feature_fig['data']
        acc_fig['layout'].update(feature_fig['layout'])
        acc_fig['layout']['yaxis2']['domain'] = [0,0.5]
        acc_fig['layout']['yaxis2']['fixedrange'] = False
        acc_fig['layout']['height'] = 600
        acc_fig['layout']['yaxis3']= dict(domain=[0.51,1])

        py.plot(acc_fig, filename=path_out+'feature_acc_graph.html')
    
    
    @staticmethod
    def preprocess(in_data, classes, target_index=None, rescale=False):
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


    @staticmethod
    def align_real_features_and_annotation(real_features, real_annotation, target_class, class_mapping=None):
        real_features = real_features.iloc[:,:18]
        if class_mapping is not None:
            real_annotation = pd.merge(real_annotation, class_mapping, left_on ='LABEL_NAME', right_on='label', copy=False).drop('LABEL_NAME', axis=1)
        truth= []
        starttimelist = real_annotation['START_TIME']
        stoptimelist = real_annotation['STOP_TIME']
    
        for key, series in real_features.iterrows():
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
    
        real_features['Truth'] = truth
        real_features = real_features.dropna()
        
        print('unknown: {} \nunwear: {}'.format(real_features[real_features['Truth'] == 'unknown'].shape[0],
        real_features[(real_features['Truth'] == 'not started') | (real_features['Truth'] == 'nonwear')].shape[0]))
        
        real_features = real_features.loc[~(real_features['Truth']=='not started'),:]    
        real_features = real_features.loc[~(real_features['Truth']=='nonwear'),:]    
        real_features = real_features.loc[~(real_features['Truth']=='unknown'),:]  
        
        return real_features
    
    
    def predict_with_real_data(self, real_features=None, class_mapping=None, real_annotation=None, target_class=None, model=None, aligned_features=None):
        if aligned_features is None:
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
            
            aligned_features = self.align_real_features_and_annotation(real_features, real_annotation, target_class, class_mapping)
            self.aligned_features = aligned_features

        prediction = model.predict(aligned_features.iloc[:,2:18])
        
        aligned_features['Result'] = prediction
                
        self.prediction= aligned_features['Result']
        self.target_data = aligned_features['Truth']
        self.feature_data = aligned_features.iloc[:,:18]

        return aligned_features['Truth'],  aligned_features['Result']
    

    @staticmethod
    def get_histograms(list_of_data, list_of_names = None, return_fig=False, mode='overlaid', path_out='/Users/zhangzhanming/Desktop/mHealth/Test/'):
        fig_list = []
        feature_names=[]
        n_traces = len(list_of_data)
        for i in range(list_of_data[0].shape[1]):
            max_val = list_of_data[0].iloc[:,i].max()
            min_val = list_of_data[0].iloc[:,i].min()
            range_val = (max_val-min_val)/100
            feature_name = list_of_data[0].columns[i]
            if range_val==0:
                # if it's a singular matrix, ignore this trace
                print('singular matrix', feature_name)
                continue
            mean = list_of_data[0].iloc[:,i].mean()
            std = list_of_data[0].iloc[:,i].std()
            start = mean-7*std
            end =  mean+7*std
            size = (end-start)/100
            feature_names.append(feature_name)
            for j in range(n_traces):
                fig_list.append(go.Histogram(
                        x=list_of_data[j].iloc[:,i],
                        histnorm='percent',
                        name=list_of_names[j],
                        opacity=0.75,
                        visible='legendonly',
                        autobinx=False,
                        xbins=dict(start=start,end=end, size=size)))
            
        if mode == 'overlaid':
            layout = go.Layout(barmode='overlay')
            fig = go.Figure(data=fig_list, layout=layout)
        
        buttons=list()
        visible = [False]*n_traces*len(feature_names)
        
        for i in range(len(feature_names)):
            new_visible = visible[:]
            
            for j in range(i*n_traces, (i+1)*n_traces):
                new_visible[j]=True
                
            buttons.append(dict(label=feature_names[i],
                                method='update',
                                args=[{'visible' : new_visible},
                                      {'title' : feature_names[i]}
                                      ]))
        buttons = list(buttons)
        updatemenus= list([
                dict(active=-1,
                     buttons=buttons)])
        fig.layout.update(dict(updatemenus=updatemenus))
        
        if return_fig:
            return fig
        py.plot(fig, filename=path_out+'histograms.html')
        
    
    def print_feature_importance(self, model=None, feature_names=None):
        if model is None:
            model = self.model
        if feature_names is None:
            feature_names = self.feature_data.columns
            if "START_TIME" in feature_names:
                feature_names = feature_names[2:18]
                
        importance = pd.DataFrame({'NAME':feature_names, 'IMPORTANCE': model.feature_importances_})
        importance.sort_values('IMPORTANCE',ascending=False, inplace=True)
        self.feature_importance = importance
        print(importance)
    
# =============================================================================
#     @staticmethod
#     def get_distribution(list_of_data, list_of_names = None, return_fig=False, path_out='/Users/zhangzhanming/Desktop/mHealth/Test/'):
#         n_traces = len(list_of_data)
#         feature_names = []
#         fig_list = []
#         for i in range(list_of_data[0].shape[1]):
#             max_val = list_of_data[0].iloc[:,i].max()
#             min_val = list_of_data[0].iloc[:,i].min()
#             size = (max_val-min_val)/100
#             feature_name = list_of_data[0].columns[i]
#             if size==0:
#                 # if it's a singular matrix, ignore this trace
#                 print('singular matrix', feature_name)
#                 continue
#             feature_list = []
#             for j in range(n_traces):
#                 feature_list.append(list_of_data[j].iloc[:,i])
#             
#             feature_names.append(feature_name)
#             print(feature_name, size)
#             fig_list.append(ff.create_distplot(feature_list, list_of_names,
#                                                           bin_size=size))
#         
#         new_fig = fig_list[0]
#         for i in range(1,len(fig_list)):
#             print(i)
#             new_fig.data += fig_list[i].data
#         
#         buttons=list()
#         visible = [False]*n_traces*len(feature_names)
#         
#         for i in range(len(feature_names)):
#             new_visible = visible[:]
#             
#             for j in range(i*n_traces, (i+1)*n_traces):
#                 new_visible[j]=True
#                 
#             buttons.append(dict(label=feature_names[i],
#                                 method='update',
#                                 args=[{'visible' : new_visible},
#                                       {'title' : feature_names[i]}
#                                       ]))
#         buttons = list(buttons)
#         updatemenus= list([
#                 dict(active=-1,
#                      buttons=buttons)])
#     
# 
# #        for i in range(len(fig.data)):
# #            fig.data[i]['visible'] = 'legendonly'
#         
#     
#         new_fig.layout.update(dict(updatemenus=updatemenus))
#         
#         if return_fig:
#             return fig
#         py.plot(new_fig, filename=path_out+'distrubition.html')
# 
#     
# =============================================================================
    

def test_on_data(position, time):
    classes = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SampleData/spadeslab/SPADESInLab-cleaned.class.csv')
    in_data = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SampleData/'+position+'.csv')
    in_data.drop(in_data.columns[0], axis =1, inplace=True)
    features, target = ModelAnalyzer.preprocess(in_data, classes, 'posture', False)
    model = RandomForestClassifier(n_estimators=50, n_jobs=-1)
    model.fit(features, target)
    scores = cross_val_score(model, features, target, cv=10)
    print('cv score:', scores.mean())
    analyzer = ModelAnalyzer(model = model)
    aiden_feature_data = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/MyData/AIDEN.'+position+'.'+time+'/Aiden/Derived/PostureAndActivity.feature.csv')
    class_mapping = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/MyData/AIDEN.'+position+'.'+time+'/Aiden/Derived/class_mapping.csv')
    real_annotation = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/MyData/AIDEN.'+position+'.'+time+'/Aiden/Derived/splitted.annotation.csv')
    analyzer.set_class_mapping(class_mapping)
    analyzer.set_real_annotation(real_annotation)
    analyzer.set_feature_data(aiden_feature_data)
    truth, prediction = analyzer.predict_with_real_data(target_class='posture')
    print('test on real data:', metrics.accuracy_score(truth, prediction))
    analyzer.gen_confusion_matrix()
    analyzer.set_root('/Users/zhangzhanming/Desktop/mHealth/Data/MyData/AIDEN.'+position+'.'+time+'/Aiden/')
    wrong_feature = analyzer.get_confusion_data('lying','sitting', get_acc_data=False)
    sample_lying = features[target=='lying']
    sample_lying = sample_lying[sample_lying.iloc[:,0] < 100]
    sample_sitting = features[target=='sitting']
    sample_sitting = sample_sitting[sample_sitting.iloc[:,0] <100]
    aligned_features = analyzer.aligned_features
    real_lying = aligned_features[aligned_features['Truth'] == 'lying']
    real_sitting = aligned_features[aligned_features['Truth'] == 'sitting']
    analyzer.print_feature_importance()
    #analyzer.plot_feature_and_raw(wrong_feature, wrong_acc)
    
    ModelAnalyzer.get_histograms([wrong_feature.iloc[:,2:18], 
                                  sample_lying, 
                                  sample_sitting, 
                                  real_lying.iloc[:,2:18], 
                                  real_sitting.iloc[:,2:18]],
                           ['wrong sitting','sample_lying','sample_sitting','real_lying','real_sitting'],
                           path_out='/Users/zhangzhanming/Desktop/mHealth/Test/'+position+'.')
    
    InterativeHistogram.gen_interactive_histograms([wrong_feature.iloc[:,:18], 
                                  sample_lying, 
                                  sample_sitting, 
                                  real_lying.iloc[:,:18], 
                                  real_sitting.iloc[:,:18]],
                           ['wrong sitting','sample_lying','sample_sitting','real_lying','real_sitting'],
                           real_annotation.iloc[:,1:])

test= False
if test:
    test_on_data('DomAnkle','2018-07-03')
    position='DomAnkle'
    time = '2018-07-03'
    
    wrong_feature.loc[(wrong_feature['MEAN_VM']>0.993878) & (wrong_feature['MEAN_VM']<0.997646),:]['MEAN_VM']
    wrong_feature.iloc[[10,26,50,52,68],:]['MEAN_VM']
    
   