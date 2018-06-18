#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 10:45:02 2018

@author: zhangzhanming
"""
import pandas as pd
import plotly.offline as py
import plotly.figure_factory as ff
import click as cli
import random
import plotly.graph_objs as go

#featuredata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/MyData/SPADES_2/Derived/Preprocessed/2015/10/08/14/ActigraphGT9X-PostureAndActivity-NA.TAS1E23150066-PostureAndActivity.2015-10-08-14-00-00-000-M0400.feature.csv')
#annotationdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/MyData/SPADES_2/MasterSynced/2015/10/08/14/SPADESInLab.alvin-SPADESInLab.2015-10-08-14-10-41-252-M0400.annotation.csv')
#pathout = '/Users/zhangzhanming/Desktop/mHealth/Test/'


def annotation_feature_grapher(featuredata, annotationdata, pathout, feature_index=None):
    # create dict of annotation data
    gantt_df = annotationdata.iloc[:,1:4]
    gantt_df.columns = ['Start','Finish','Task']
    gantt_df['Resource'] = gantt_df['Task']
    colors =  __generate_color(len(gantt_df['Resource'].unique()))
    gantt_fig = ff.create_gantt(gantt_df, group_tasks=True, bar_width=0.7, 
                                   title='annotation', index_col='Resource',
                                   colors=colors,show_colorbar=True, width=1200)
    
    # create line chart for selected features
    if feature_index is None:
        feature_index = [2,3,4] 
    
    traces = []
    for index in feature_index:
        trace = go.Scatter(x = featuredata[featuredata.columns[0]],
                           y = featuredata[featuredata.columns[index]],
                           name = featuredata.columns[index],
                           mode = 'lines+markers')
        traces.append(trace)
    
    gantt_fig['data'] = gantt_fig['data']+traces
    
    # move all the labels up
    newshape = gantt_fig['layout']['shapes']
    for label in newshape:
        label['y0'] +=5
        label['y1'] +=5
        label['opacity'] = 0.5
    
    gantt_fig['layout']['shapes'] = newshape
    newyaxis = gantt_fig['layout']['yaxis']
    newrange = newyaxis['range']
    tickvals = newyaxis['tickvals']
    newyaxis['tickvals'] = [x + 5 for x in tickvals ]
    newyaxis['range'] = [newrange[0], newrange[1]+5]
    gantt_fig['layout']['yaxis'] = newyaxis
    
    py.plot(gantt_fig, filename=(pathout+'test.html'))
    

def __generate_color(n):
    colors = []
    for i in range(n):
        r = int(random.random() * 256)
        g = int(random.random() * 256)
        b = int(random.random() * 256)
        colors.append('rgb('+','.join([str(r),str(g),str(b)])+')') 
    return colors
    