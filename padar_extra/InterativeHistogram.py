#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 11:41:41 2018

@author: zhangzhanming
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from textwrap import dedent as d
import json
import Visualizer
import ast
import pandas as pd
import copy


def gen_interactive_histograms(testing_data, training_data, list_of_names, annotations, feature_names=None, classes=None):
    app = dash.Dash()
    if feature_names is None:
        feature_names = testing_data[0].columns
        if "START_TIME" in feature_names:
            feature_names = feature_names[2:18]
        
    ann_fig = Visualizer.annotation_feature_grapher(annotations, return_fig=True, non_overlap=True)
    all_shapes = []
    for index, series in testing_data[0].iloc[:,:2].iterrows():
            all_shapes.append(
                    {'type': 'rect',
                     'xref': 'x',
                     'yref': 'paper',
                     'x0': series[0],
                     'y0': 0,
                     'x1': series[1],
                     'y1': 1,
                     'fillcolor': '#FF3383',
                     'opacity': 0.5,
                     'line': {
                        'width': 0,
                     }
                    })

    clicked=0
    
    styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
        }
    }
    
# =============================================================================
#     if classes is None:
#         classes = list(testing_data[0].iloc[:,-1].unique())
# =============================================================================
    
    
    app.layout = html.Div([
            
            html.Div([
                    dcc.Dropdown(
                            id='feature-kind',
                            options=[{'label': feature_names[i], 'value': feature_names[i]} for i in range(len(feature_names))],
                            value= 'MEAN_VM'),
# =============================================================================
#                     dcc.Checklist(options=[
#                             {'label':}
#                             
#                             ]])
# =============================================================================
    ]),
            html.Div([
                    dcc.Graph(
                            id='histograms',
                            )]),
            html.Div(className='row', children=[
                html.Div([
                    html.Button('Show All', id='button'),
                    dcc.Graph(id='annotation', figure=ann_fig),
                    ##html.Pre(id='hover-data', style=styles['pre'])
                ], className='three columns')],
            )
    ])
    
    
    @app.callback(
            dash.dependencies.Output('histograms','figure'),
            [dash.dependencies.Input('feature-kind','value')])
    def update_histograms(feature_kind):
        fig_list = []
        list_of_data = testing_data + training_data
        n_traces = len(list_of_data)
        max_val = list_of_data[0].loc[:,feature_kind].max()
        min_val = list_of_data[0].loc[:,feature_kind].min()
        range_val = (max_val-min_val)/100
        feature_name = feature_kind
        if range_val==0:
            # if it's a singular matrix, ignore this trace
            print('singular matrix', feature_name)
            return None
# =============================================================================
#         mean = list_of_data[0].loc[:,feature_kind].mean()
#         std = list_of_data[0].loc[:,feature_kind].std()
#         start = mean-7*std
#         end =  mean+7*std
#         size = (end-start)/100
# =============================================================================
        start = min([min(data.loc[:,feature_kind]) for data in list_of_data])
        end = max([max(data.loc[:,feature_kind]) for data in list_of_data])
        size = (end-start)/100
        for j in range(n_traces):
            fig_list.append(go.Histogram(
                    x=list_of_data[j].loc[:,feature_kind],
                    histnorm='percent',
                    name=list_of_names[j],
                    opacity=0.5,
                    visible='legendonly',
                    autobinx=False,
                    xbins=dict(start=start,end=end, size=size)))
        layout = go.Layout(barmode='overlay')
        fig = go.Figure(data=fig_list, layout=layout)
        
        return fig
    
    
# =============================================================================
#     @app.callback(
#         dash.dependencies.Output('hover-data', 'children'),
#         [dash.dependencies.Input('histograms', 'clickData')])
#     def display_hover_data(hoverData):
#         return json.dumps(hoverData, indent=2)
#     
# =============================================================================
    @app.callback(
        dash.dependencies.Output('annotation', 'figure'),
        [dash.dependencies.Input('histograms', 'clickData'),
         dash.dependencies.Input('button','n_clicks')])
    def update_annotation(clickData, n_clicks): 
        new_fig = copy.deepcopy(ann_fig)
        nonlocal clicked
        if n_clicks is not None and n_clicks > clicked:
            clicked = n_clicks
            new_fig['layout']['shapes'] += all_shapes
            return new_fig
            
        if clickData is None: return new_fig
        indexes = dict()
        
        for point in clickData['points']:
            if point['curveNumber'] < len(testing_data):
                indexes[point['curveNumber']] = point['pointNumbers']
        
        time_series = pd.DataFrame(columns=['START_TIME','STOP_TIME'])
        for key in indexes.keys():
            time_series = time_series.append(testing_data[key].iloc[indexes[key],:2])
        shapes = []
        for index, series in time_series.iterrows():
            shapes.append(
                    {'type': 'rect',
                     'xref': 'x',
                     'yref': 'paper',
                     'x0': series[0],
                     'y0': 0,
                     'x1': series[1],
                     'y1': 1,
                     'fillcolor': '#FF3383',
                     'opacity': 0.5,
                     'line': {
                        'width': 0,
                     }
                    })
        new_fig['layout']['shapes'] += shapes
        return new_fig
        
        
    app.run_server()


           
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    