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

def gen_interactive_histograms(annotations, testing_data = [], training_data = [], list_of_names = None, 
                               all_testing = None, all_training = None, 
                               feature_names=None, classes=None):
    
    """
    Create an interactive graph which has the histograms of features and 
    a spectrum graph of annotations.
    For more information, see https://github.com/codeconomics/DataTools/edit/master/ReadMe.md
    
    Args:
        annotations: filepath or pandas.DataFrame annotation file in mHealth format
        testing_data: a list of testing datasets to visualize initially, default []
        training_data: a list of training datasets to visualize initially, default []
        list_of_names: a list of names assigned to testing_data and training_data passed, default []
        all_testing: filepath or pandas.DataFrame the whole testing features dataset in mHealth format with 
            prediction result in 'Result' column and ground truth in 'Truth' columnn
        all_training: filepath or pandas.DataFrame the whole training features dataset in mHealth format with 
            ground truth in 'Truth' column
        feature_names: a list of feature name strings to indicate the order to display in drop down selectio
            menu, default []
        classes: a list of classes existing in classification to visualize. Default [] to select all 
            exisiting unique classes
    
    """
    
    if isinstance(annotations, str):
        annotations = pd.read_csv(annotations)
    
    if isinstance(all_testing, str):
        all_testing = pd.read_csv(all_testing)
    
    if isinstance(all_training, str):
        all_training = pd.read_csv(all_training)
    
    # remove header time from annotations
    annotations = annotations.iloc[:,1:]
    
    if len(testing_data) == 0 and all_testing is None:
        raise Exception('No testing data provided')
        
    if len(training_data) == 0 and all_training is None:
        raise Exception('No training data provided')
    
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
    
    if len(testing_data) > 0:
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

    show_all_clicked=0
    submit_clicked=0
    
    styles = {
        'dropdown-selection' : {
                'fontFamily' : 'Arial, Helvetica, sans-serif',
                'width': '49%', 
                'display': 'inline-block', 
                'vertical-align': 'middle',
                'padding': 2
                },

        'property-selection' : {
                'backgroundColor': 'AliceBlue',
                },
        
        'submit-botton' : {
                'padding':2}
    }
    
    # change the default style for dropdown menu and buttons
    app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
    
    if classes is None and all_testing is not None:
        classes = list(all_testing.iloc[:,-1].unique())
    
    options = [{'label': x, 'value': x} for x in classes]
    
    
    app.layout = html.Div([
            
            html.Div([
                    html.Div([
                        html.Label('SELECT FEATURE'),
                        dcc.Dropdown(
                                id='feature-kind',
                                options=[{'label': feature_names[i], 'value': feature_names[i]} for i in range(len(feature_names))],
                                value= 'MEAN_VM'),
                        html.Label('SELECT GROUND TRUTH'),
                        dcc.Dropdown(
                                id='truth-class',
                                options=options,
                                ),
                        ],
                        style=styles['dropdown-selection']
                    ),
                    html.Div([
                        html.Label('SELECT PREDICTION'),
                        dcc.Dropdown(
                                id='result-class',
                                options=options,
                                ),
                        #html.Pre(id='class-selection', style=styles['pre']),
                        html.Div(
                                [html.Button('SUBMIT', id='submit-button')],
                                
                        style= styles['submit-botton'])
                        ],
                        style=styles['dropdown-selection']
                    )
            ], style=styles['property-selection']),
    
            html.Div([
                    dcc.Graph(
                            id='histograms',
                            )]),
            html.Div(className='row', children=[
                html.Div([
                    html.Button('Show All Misclassified', id='show-all-button'),
                    dcc.Graph(id='annotation', figure=ann_fig),
                    ##html.Pre(id='hover-data', style=styles['pre'])
                ], className='three columns')],
            )
    ])
    
      
    
    @app.callback(
            dash.dependencies.Output('histograms','figure'),
            [dash.dependencies.Input('feature-kind','value'),
             dash.dependencies.Input('submit-button','n_clicks')],
             [dash.dependencies.State('truth-class','value'),
             dash.dependencies.State('result-class','value'),])
    def update_histograms(feature_kind, update_trigger, truth, result):
        nonlocal submit_clicked

        if update_trigger is not None and update_trigger > submit_clicked:
            nonlocal testing_data
            nonlocal training_data
            nonlocal list_of_names
            submit_clicked = update_trigger
            testing_data = []
            training_data = []
            list_of_names = []
            testing_data.append(all_testing.loc[(all_testing['Truth'] == truth) &
                                (all_testing['Result'] == result),:])
            list_of_names.append(truth + ' to ' + result)
        
            testing_data.append(all_testing.loc[(all_testing['Truth'] == truth) &
                                (all_testing['Result'] == truth),:])
            list_of_names.append('testing correct ' + truth)
            
            testing_data.append(all_testing.loc[all_testing['Truth'] == result,:])
            list_of_names.append('testing ' + result)
    
            training_data.append(all_training.loc[all_training['Truth'] == truth,:])
            training_data.append(all_training.loc[all_training['Truth'] == result,:])
            list_of_names.append('training '+ truth)
            list_of_names.append('training '+ result)
            
            # everytime changed feature selection, update default annotation high light
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
        if n_traces < 1:
            return None
        max_val = list_of_data[0].loc[:,feature_kind].max()
        min_val = list_of_data[0].loc[:,feature_kind].min()
        range_val = (max_val-min_val)/100
        feature_name = feature_kind
        if range_val==0:
            # if it's a singular matrix, ignore this trace
            print('singular matrix', feature_name)
            return None

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
         dash.dependencies.Input('show-all-button','n_clicks'),
         dash.dependencies.Input('submit-button','n_clicks')])
    def update_annotation(clickData, n_clicks, update_trigger): 
        new_fig = copy.deepcopy(ann_fig)
        nonlocal show_all_clicked
        if n_clicks is not None and n_clicks > show_all_clicked:
            show_all_clicked = n_clicks
    
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



        
        
        
        
        
        
        
        
        
        
        
        
        
        
    