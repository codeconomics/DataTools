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
DISPLAY_RANGE = 76.8
TIME_PERIOD = 200
FEATURE_TIME = 12.8
annotation_colors={}

app = dash.Dash('Live Stream Feature')
monitor = Monitor.Monitor()
db = Monitor.AccDataBase(monitor)
monitor.register_observer(db)
monitor.listen()

app.layout = html.Div([html.H2('Streaming Features'),
                       html.Div([
                               dcc.Graph(id='acceleration-graph'),
                               ]),
                       dcc.Interval(id='time-update', interval=TIME_PERIOD, n_intervals=0)])


@app.callback(Output('acceleration-graph','figure'),
              [Input('time-update','n_intervals')])
def gen_acceleration_graph(count):
    acc_end = len(db.rawdata.index)
    acc_start = int(acc_end - DISPLAY_RANGE*SAMPLING_RATE)

    if acc_start < 0:
        acc_start = 0

    acc_data = db.rawdata[acc_start:acc_end]

# =============================================================================
#     if acc_start != acc_end and len(acc_data.index) < DISPLAY_RANGE*SAMPLING_RATE:
#         diff = DISPLAY_RANGE*SAMPLING_RATE-acc_data.shape[0]
#         diff_range = pd.date_range(end=acc_data.iloc[0, 0],
#                                    periods=diff,
#                                    freq=str(int(1000/SAMPLING_RATE))+'L')
#         diff_df = pd.DataFrame(data={acc_data.columns[0]: diff_range.values,
#                                      acc_data.columns[1]: [None] * diff_range.shape[0],
#                                      acc_data.columns[2]: [None] * diff_range.shape[0],
#                                      acc_data.columns[3]: [None] * diff_range.shape[0]})
# 
#         acc_data = pd.concat([diff_df, acc_data])
# 
# =============================================================================
    #print(acc_data.tail())

    acc_fig = Visualizer.acc_grapher(acc_data,return_fig=True)

    feature_end = len(db.featuredata.index)
    feature_start = int(feature_end - DISPLAY_RANGE/FEATURE_TIME) - 1

    if feature_start < 0:
        feature_start = 0
    if feature_end < 0:
        feature_end = 0

    feature_data = db.featuredata.iloc[feature_start:feature_end,:]

# Filling empty values might be unneccessary
# =============================================================================
#     if feature_start != feature_end and len(feature_data.index) < DISPLAY_RANGE/FEATURE_TIME:
# 
#         diff = int(DISPLAY_RANGE/FEATURE_TIME) - feature_data.shape[0]
#         diff_range_stop = pd.date_range(end=feature_data.iloc[0,0],
#                                    periods=diff,
#                                    freq=(str(FEATURE_TIME)+'S'))
#         diff_range_start = pd.date_range(end=feature_data.iloc[0,0],
#                                    periods=diff+1,
#                                    freq=(str(FEATURE_TIME)+'S'))[0:diff]
# 
#         data_dict = OrderedDict()
#         for column_name in feature_data.columns:
#             data_dict[column_name] = [None] * diff_range_start.shape[0]
# 
#         data_dict[feature_data.columns[0]] = diff_range_start.values.flatten()
#         data_dict[feature_data.columns[1]] = diff_range_stop.values.flatten()
#         diff_df = pd.DataFrame(data = data_dict)
# 
# 
#         feature_data = pd.concat([diff_df, feature_data])
# 
# 
#     if feature_start == feature_end and acc_data.shape[0] != 0:
#         data_dict = OrderedDict()
#         for column_name in feature_data.columns:
#             data_dict[column_name] = [None]
# 
#         data_dict[feature_data.columns[0]] = acc_data.iloc[0,0]
#         data_dict[feature_data.columns[1]] = acc_data.iloc[0,1]
#         feature_data = pd.DataFrame(data = data_dict)
# 
# =============================================================================
    feature_fig = Visualizer.feature_grapher(feature_data, return_fig=True)
    #print(db.annotationdata.iloc[:,[0,1,2,5]])
    
    for label in db.annotationdata.iloc[:,5].unique():
        if label not in annotation_colors:
            annotation_colors[label] = Visualizer.generate_color(1)[0]
    
    annotation_fig = Visualizer.annotation_feature_grapher(db.annotationdata.iloc[:,[0,1,2,5]], 
                                                           return_fig=True,
                                                           colors=annotation_colors)
    
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

