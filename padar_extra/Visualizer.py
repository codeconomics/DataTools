#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 10:45:02 2018

@author: zhangzhanming
"""
import pandas as pd
import plotly.offline as py
import plotly.figure_factory as ff
import random
import plotly.graph_objs as go
import sys
import ast
import os.path
from plotly import tools


def annotation_feature_grapher(featuredata, annotationdata, path_out=None, feature_index=None, return_fig=False):
    """

    Create a figure with selected features(if no feature index is passed, select 
    all Features by default), and annotation. if not return figure object, 
    create html file in designated file path

    Args:
        featuredata: pandas.DataFrame containing feature data
        annotationdata: pandas.DataFrame containing annotations
        pathout: path to write the html figure file
        feature_index: the index of the features to select in featuredata dataframe
        return_fig: if return the figure object

    Returns:
        if return_fig == False: the url of the created figure 
        else return the figure object
        

    """
    if isinstance(featuredata, str):
        featuredata = pd.read_csv(featuredata)
    elif featuredata is None:
        featuredata = None
    if isinstance(annotationdata, str):
        annotationdata = pd.read_csv(annotationdata)
    if isinstance(feature_index, str):
        feature_index = ast.literal_eval(feature_index)

    # create dict of annotation data
    gantt_df = annotationdata.iloc[:,1:4]
    gantt_df.columns = ['Start','Finish','Task']
    gantt_df['Resource'] = gantt_df['Task']
    colors =  __generate_color(len(gantt_df['Resource'].unique()))
    gantt_fig = ff.create_gantt(gantt_df, group_tasks=True, bar_width=0.7,
                                   title='Features And Annotation', index_col='Resource',
                                   colors=colors, width=1300, show_colorbar=True)

    # create line chart for selected features
    if featuredata is not None:
        if feature_index is None:
            feature_index = range(2,17)

        traces = []
        for index in feature_index:
            trace = go.Scatter(x = featuredata[featuredata.columns[0]],
                            y = featuredata[featuredata.columns[index]],
                            name = featuredata.columns[index],
                            mode = 'lines+markers',
                            yaxis='y2')
            traces.append(trace)

        newdata = gantt_fig['data']
        for line in newdata:
            if 'y' in line:
                line['y'] = [line['y'][0]+5,line['y'][1]+5]
        #    if 'hoverinfo' in line:
        #        line['text'] = line['name']
        #        line['hoverinfo'] = 'text'

        gantt_fig['data'] = newdata+traces

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
    
    if featuredata is not None:
        yaxis2=dict(
            titlefont=dict(
                color='rgb(148, 103, 189)'
            ),
            tickfont=dict(
                color='rgb(148, 103, 189)'
            ),
            overlaying='y',
            side='right'
        )
        gantt_fig['layout'].update({'yaxis2': yaxis2})

    if return_fig:
        return gantt_fig
    
    if os.path.isdir(path_out):
        path_out = path_out + '/'

    return py.plot(gantt_fig, filename=(path_out+'feature_annotation_graph.html'))

def acc_grapher(data, path_out=None, return_fig = False):
    """
    
    Create a figure with acceleration data, if return_fig is true, return the
    figure object, otherwise return the url
    
    Args:
        data: pandas.Dataframe containing acceleration data
        path_out: string the path to write
        return_fig: if return the figure object
    
    """
    
    x = go.Scatter(
            y=data['X_ACCELERATION_METERS_PER_SECOND_SQUARED'],
            x=data['HEADER_TIME_STAMP'],
            name='x',
            mode='lines')

    y = go.Scatter(
            y=data['Y_ACCELERATION_METERS_PER_SECOND_SQUARED'],
            x=data['HEADER_TIME_STAMP'],
            name='y',
            mode='lines')

    z = go.Scatter(
            y=data['Z_ACCELERATION_METERS_PER_SECOND_SQUARED'],
            x=data['HEADER_TIME_STAMP'],
            name='z',
            mode='lines')

    layout=dict(yaxis = dict(fixedrange=True, range=[-5,5]),
                xaxis = dict(tickformat='%H:%M:%S',
                             nticks=5))
    fig = dict(data=[x,y,z], layout=layout)
    
    if return_fig:
        return fig
    
    if os.path.isdir(path_out):
        path_out = path_out + '/'

    return py.plot(fig, filename=path_out+'acc_graph.html')


def __generate_color(n):
    colors = []
    for i in range(n):
        r = int(random.random() * 256)
        g = int(random.random() * 256)
        b = int(random.random() * 256)
        colors.append('rgb('+','.join([str(r),str(g),str(b)])+')')
    return colors

if __name__ == '__main__':
    if len(sys.argv) <4:
        print('INSTRUCTION: [feature data file] [annotatoin data file] [pathout] [feature list]')
    else:
        if len(sys.argv) == 4:
            annotation_feature_grapher(sys.argv[1],sys.argv[2],sys.argv[3])
        else:
            annotation_feature_grapher(sys.argv[1],sys.argv[2],sys.argv[4])
