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
import Visualizer
import pandas as pd
import copy


def gen_interactive_histograms(testing_data, training_data, list_of_names, annotations, 
                               all_testing = None, all_training = None, show_all_data=False,
                               feature_names=None, classes=None):
    app = dash.Dash()
    if feature_names is None:
        if len(testing_data) > 0:
            feature_names = testing_data[0].columns
        elif all_testing is not None:
            feature_names = all_testing.columns
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
    button_clicked=0
    
    styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
        }
    }
    
    if classes is None and all_testing is not None:
        classes = list(all_testing.iloc[:,-1].unique())
    
    options = [{'label': x, 'value': x} for x in classes]
    
    
    app.layout = html.Div([
            
            html.Div([
                    dcc.Dropdown(
                            id='feature-kind',
                            options=[{'label': feature_names[i], 'value': feature_names[i]} for i in range(len(feature_names))],
                            value= 'MEAN_VM'),
                    dcc.Dropdown(
                            id='truth-class',
                            options=options,
                            ),
                    dcc.Dropdown(
                            id='result-class',
                            options=options,
                            ),
                    html.Pre(id='class-selection', style=styles['pre']),
                    html.Button('submit', id='submit-button'),
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
            dash.dependencies.Output('class-selection','children'),
            [dash.dependencies.Input('submit-button','n_clicks')],
            [dash.dependencies.State('truth-class','value'),
             dash.dependencies.State('result-class','value'),])
    def update_class_selection(update_trigger, truth, result):
# =============================================================================
#         nonlocal testing_data
#         nonlocal training_data
#         nonlocal list_of_names
# =============================================================================
        if truth is not None and result is not None:
# =============================================================================
#             testing_data = []
#             training_data = []
#             list_of_names = []
#             testing_data.append(all_testing.loc[(all_testing['Truth'] == truth) &
#                                 (all_testing['Result'] == result),:])
#             list_of_names.append(truth + ' to ' + result)
#         
#             testing_data.append(all_testing.loc[all_testing['Truth'] == truth,:])
#             list_of_names.append('testing ' + truth)
#             
#             testing_data.append(all_testing.loc[all_testing['Truth'] == result,:])
#             list_of_names.append('testing ' + result)
#     
#             training_data.append(all_training.loc[all_training['Truth'] == truth,:])
#             training_data.append(all_training.loc[all_training['Truth'] == result,:])
#             list_of_names.append('training '+ truth)
#             list_of_names.append('training '+ result)
#             print(list_of_names)
# =============================================================================
            return 'Showing {} classified as {}'.format(truth, result)
        
        return ""
    
    
    
    @app.callback(
            dash.dependencies.Output('histograms','figure'),
            [dash.dependencies.Input('feature-kind','value'),
             dash.dependencies.Input('submit-button','n_clicks')],
             [dash.dependencies.State('truth-class','value'),
             dash.dependencies.State('result-class','value'),])
    def update_histograms(feature_kind, update_trigger, truth, result):
        nonlocal button_clicked
        if update_trigger is not None and update_trigger > button_clicked:
            nonlocal testing_data
            nonlocal training_data
            nonlocal list_of_names
            button_clicked = update_trigger
            testing_data = []
            training_data = []
            list_of_names = []
            testing_data.append(all_testing.loc[(all_testing['Truth'] == truth) &
                                (all_testing['Result'] == result),:])
            list_of_names.append(truth + ' to ' + result)
        
            testing_data.append(all_testing.loc[all_testing['Truth'] == truth,:])
            list_of_names.append('testing ' + truth)
            
            testing_data.append(all_testing.loc[all_testing['Truth'] == result,:])
            list_of_names.append('testing ' + result)
    
            training_data.append(all_training.loc[all_training['Truth'] == truth,:])
            training_data.append(all_training.loc[all_training['Truth'] == result,:])
            list_of_names.append('training '+ truth)
            list_of_names.append('training '+ result)
            
            nonlocal all_shapes
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
        print(feature_kind)
        start = min([min(data.loc[:,feature_kind]) for data in list_of_data])
        end = max([max(data.loc[:,feature_kind]) for data in list_of_data])
        print(start, end)
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
         dash.dependencies.Input('button','n_clicks'),
         dash.dependencies.Input('submit-button','n_clicks')])
    def update_annotation(clickData, n_clicks, update_trigger): 
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


           
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    