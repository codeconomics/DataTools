#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 15:00:59 2018

@author: zhangzhanming
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
import Visualizer
import Monitor
from collections import OrderedDict
from plotly import tools
import datetime


SAMPLING_RATE = 80
DISPLAY_RANGE = 64
TIME_PERIOD = 500
FEATURE_TIME = 12.8
annotation_colors={}

app = dash.Dash('Live Stream Feature')
monitor = Monitor.Monitor()
db = Monitor.AccDataBase(monitor)
monitor.register_observer(db)
monitor.listen()
feature_options=[]
for feature in db.feature_columns:
    feature_options.append(dict(label=feature, value=feature))
app.layout = html.Div([html.H2('Streaming Features'),
                       html.Div([
                               dcc.Graph(id='acceleration-graph'),
                               ]),
                       dcc.Interval(id='time-update', interval=TIME_PERIOD, n_intervals=0),
                        ])
                       #html.Div([html.H3('Select feature'),
                        #         dcc.Dropdown(options=feature_options,
                         #                     multi=True)])])


@app.callback(Output('acceleration-graph','figure'),
              [Input('time-update','n_intervals')])
def gen_acceleration_graph(count):
    acc_end = len(db.rawdata.index)
    acc_start = int(acc_end - DISPLAY_RANGE*SAMPLING_RATE)

    if acc_start < 0:
        acc_start = 0

    acc_data = db.rawdata[acc_start:acc_end]

    acc_fig = Visualizer.acc_grapher(acc_data,return_fig=True)

    feature_end = len(db.featuredata.index)
    feature_start = int(feature_end - DISPLAY_RANGE/FEATURE_TIME) - 1

    if feature_start < 0:
        feature_start = 0
    if feature_end < 0:
        feature_end = 0

    feature_data = db.featuredata.iloc[feature_start:feature_end,:]
    feature_fig = Visualizer.feature_grapher(feature_data, return_fig=True)
    
    for label in db.annotationdata.iloc[:,3].unique():
        if label not in annotation_colors:
            annotation_colors[label] = Visualizer.generate_color(1)[0]
    
    annotation_end = len(db.annotationdata.index)
    annotation_start = int(annotation_end - DISPLAY_RANGE/FEATURE_TIME) - 1

    if annotation_start < 0:
        annotation_start = 0
    if annotation_end < 0:
        annotation_end = 0

    annotation_data = db.annotationdata.iloc[annotation_start:annotation_end,:]
    annotation_fig = Visualizer.annotation_feature_grapher(annotation_data.iloc[:,[0,1,3]], colors=annotation_colors, return_fig=True)
    
    
    acc_fig['data'] += feature_fig['data']
    acc_fig['data'] += annotation_fig['data']

    acc_fig['layout'].update(feature_fig['layout'])

    acc_fig['layout'].update(annotation_fig['layout'])
    acc_fig['layout']['yaxis']['domain'] = [0,0.3]
    acc_fig['layout']['yaxis2']['domain'] = [0.31,0.6]
    acc_fig['layout']['yaxis3']['domain'] = [0.61, 1]

    range_end = pd.to_datetime(acc_data.iloc[acc_data.shape[0]-1,0])
    range_start = range_end - datetime.timedelta(seconds=DISPLAY_RANGE)
    acc_fig['layout']['xaxis'].update(dict(fixedrange=True, range=[range_start,range_end]))
    acc_fig['layout']['width'] = 1200

    return acc_fig


if __name__ == '__main__':
    app.run_server()

