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
import datetime as dt
import numpy as np



def annotation_feature_grapher(annotationdata, featuredata=None, path_out=None, 
                               feature_index=None, return_fig=False, title='', colors=None,
                               non_overlap=False, show_colorbar=True):
    """

    Create a figure with selected features(if no feature index is passed, select
    all Features by default), and annotation. if not return figure object,
    create html file in designated file path

    Args:
        annotationdata: pandas.DataFrame containing annotations
        featuredata: pandas.DataFrame containing feature data
        path_out: path to write the html figure file
        feature_index: the index of the features to select in featuredata dataframe
        return_fig: if return the figure object
        titile: the title of the graph. Default empty string
        colors: preset colors for different labels. If empty generate random colors
        non_overlap: boolean indicate if annotations have overlaps. If True, will create
            a spectrum graph for annotations
        show_colorbar: if show legend

    Returns:
        if return_fig == False: the url of the created figure
        else return the figure object


    """

    if featuredata is None:
        featuredata = None
    elif isinstance(featuredata, str):
        featuredata = pd.read_csv(featuredata)
    if isinstance(annotationdata, str):
        annotationdata = pd.read_csv(annotationdata)
    if isinstance(feature_index, str):
        feature_index = ast.literal_eval(feature_index)
    
    # create dict of annotation data
    annotationdata.reset_index(drop=True, inplace=True)
    if annotationdata.shape[0] > 0:
        try:
            test_date_time = pd.to_datetime(annotationdata.iloc[0,2])
            if isinstance(test_date_time, dt.datetime):
                annotationdata = annotationdata.iloc[:,1:]
        except:
            pass
        
        
        gantt_df = annotationdata.iloc[:,:3]
        gantt_df.columns = ['Start','Finish','Task']
        gantt_df['Resource'] = gantt_df['Task']
        if colors == None:
            colors =  generate_color(len(gantt_df['Resource'].unique()))
        gantt_fig = ff.create_gantt(gantt_df, group_tasks=True, bar_width=0.7,
                                       title=title, index_col='Resource',
                                       colors=colors, show_colorbar=show_colorbar)
        gantt_fig['layout']['hovermode'] = 'closest'
        
        if non_overlap:
            for box in gantt_fig['layout']['shapes']:
                box['y0'] = 0.2
                box['y1'] = 1.8
                box['yref'] = 'page'
            tick_text = gantt_fig['layout']['yaxis']['ticktext']

            for point in gantt_fig['data']:
                point['text'] = tick_text[point['y'][0]]
                point['y'] = [1,1]
                point['hoverinfo'] = 'text'
                point['mode'] = 'lines+markers',
                point['hoveron'] = 'points+fills'

            
            del gantt_fig['layout']['yaxis']['tickvals']
            del gantt_fig['layout']['yaxis']['ticktext']
            gantt_fig['layout']['yaxis']['range'] = [0,2]
            gantt_fig['layout']['height'] = 250
            gantt_fig['layout']['width'] = 1200
            gantt_fig['layout']['showlegend'] = False
            gantt_fig['layout']['yaxis']['showline']=False
            gantt_fig['layout']['yaxis']['showticklabels']=False

        
        
        if featuredata is None and return_fig:
            return gantt_fig
    else:
        place_holder = pd.DataFrame({'START_TIME':np.datetime64('1971-01-01'), 
                                     'TEMP':0}, index=[0])
        gantt_fig = dict(data=[go.Scatter(x=place_holder[place_holder.columns[0]], 
                                 y=place_holder[place_holder.columns[1]], 
                                 showlegend=False)],
                    layout=dict(yaxis=dict(range=[-1,33])), showgrid=False, height=600)
        return gantt_fig

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
                            yaxis='y2',
                            showlegend=True,
                            visible='legendonly')
            traces.append(trace)

        newdata = gantt_fig['data']
        for line in newdata:
            if 'y' in line:
                line['y'] = [line['y'][0]+5,line['y'][1]+5]
                
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


def acc_grapher(data, path_out=None, return_fig = False, showlegend=False):
    """

    Create a figure with acceleration data, if return_fig is true, return the
    figure object, otherwise return the url

    Args:
        data: pandas.Dataframe containing acceleration data
        path_out: string the path to write
        return_fig: if return the figure object
        
    Returns:
        if return_fig == False: the url of the created figure
        else return the figure object
        

    """
    
    x = go.Scatter(
            y=data['X_ACCELERATION_METERS_PER_SECOND_SQUARED'],
            x=data['HEADER_TIME_STAMP'],
            name='x',
            mode='lines',
            yaxis='y2',
            showlegend=showlegend)

    y = go.Scatter(
            y=data['Y_ACCELERATION_METERS_PER_SECOND_SQUARED'],
            x=data['HEADER_TIME_STAMP'],
            name='y',
            mode='lines',
            yaxis='y2',
            showlegend=showlegend)

    z = go.Scatter(
            y=data['Z_ACCELERATION_METERS_PER_SECOND_SQUARED'],
            x=data['HEADER_TIME_STAMP'],
            name='z',
            mode='lines',
            yaxis='y2',
            showlegend=showlegend)

    layout=dict(yaxis2 = dict(fixedrange=True, range=[-5,5]),
                xaxis = dict(tickformat='%H:%M:%S',
                             nticks=5),
                height=400,
                hovermode='closest')
    fig = dict(data=[x,y,z], layout=layout)

    if return_fig:
        return fig

    if os.path.isdir(path_out):
        path_out = path_out + '/'

    return py.plot(fig, filename=path_out+'acc_graph.html')


def feature_grapher(featuredata, feature_index = None, path_out=None, return_fig=False, showlegend=False, hide_traces=False):
    """

    Create a figure with feature data, if return_fig is true, return the
    figure object, otherwise return the url

    Args:
        data: pandas.Dataframe containing feature data
        feature_index: the index of features to plot
        path_out: string the path to write
        return_fig: if return the figure object

    Returns:
        if return_fig == False: the url of the created figure
        else return the figure object

    """
    traces = []
    if hide_traces:
        visible= 'legendonly'
    else:
        visible=True
        
    if featuredata.shape[0] > 0:
        if feature_index is None:
           feature_index = range(2,18)
    
        for index in feature_index:
            trace = go.Scatter(
                            x = pd.to_datetime(featuredata.iloc[:,1]),
                            y = featuredata.iloc[:,index],
                            name = featuredata.columns[index],
                            mode = 'lines+markers',
                            yaxis='y3',
                            showlegend=showlegend,
                            line=dict(
                            shape='vh'),
                            visible=visible)
            traces.append(trace)
    else:
        place_holder = pd.DataFrame({'START_TIME':np.datetime64('1971-01-01'), 
                                     'TEMP':0}, index=[0])
        traces.append(go.Scatter(x=place_holder[place_holder.columns[0]], 
                                 y=place_holder[place_holder.columns[1]], 
                                 mode = 'lines+markers',
                                 showlegend=showlegend,
                                 yaxis='y3',
                                 visible=visible))
    layout = dict(height=600)
    fig = dict(data = traces, layout=layout)

    if return_fig:
         return fig

    if os.path.isdir(path_out):
        path_out = path_out + '/'

    return py.plot(fig, filename=path_out+'feature_graph.html')


def generate_color(n):
    """
    Generate a list of n random colors
    
    Args:
        n: int number of random colors to generate
    
    Returns:
        a list of random colors
    
    """

    colors = []
    for i in range(n):
        r = int(random.random() * 256)
        g = int(random.random() * 256)
        b = int(random.random() * 256)
        colors.append('rgb('+','.join([str(r),str(g),str(b)])+')')
    return colors

if __name__ == '__main__':
    if len(sys.argv) <4:
        print('INSTRUCTION: [annotatoin data file] [feature data file] [pathout] [feature list]')
    else:
        if len(sys.argv) == 4:
            annotation_feature_grapher(sys.argv[1],sys.argv[2],sys.argv[3])
        else:
            annotation_feature_grapher(sys.argv[1],sys.argv[2],sys.argv[4])
