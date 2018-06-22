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

SAMPLING_RATE = 80
DISPLAY_RANGE = 20
TIME_PERIOD = 200

app = dash.Dash('Live Stream Feature')
monitor = Monitor.Monitor()
db = Monitor.AccDataBase(monitor)
monitor.register_observer(db)
monitor.listen()
# =============================================================================
# featuredata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/Derived/Preprocessed/2015/10/08/14/ActigraphGT9X-PostureAndActivity-NA.TAS1E23150066-PostureAndActivity.2015-10-08-14-00-00-000-M0400.feature.csv')
# annotationdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/MasterSynced/2015/10/08/14/SPADESInLab.alvin-SPADESInLab.2015-10-08-14-10-41-252-M0400.annotation.csv')
# rawdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/MasterSynced/2015/10/08/14/ActigraphGT9X-AccelerationCalibrated-NA.TAS1E23150066-AccelerationCalibrated.2015-10-08-14-00-00-000-M0400.sensor.csv')
# 
# =============================================================================


app.layout = html.Div([html.H2('Streaming Features'),
                       html.Div([
                               dcc.Graph(id='acceleration-graph'),
                               ]),
                       dcc.Interval(id='time-update', interval=TIME_PERIOD, n_intervals=0)])


@app.callback(Output('acceleration-graph','figure'), 
              [Input('time-update','n_intervals')])
def gen_acceleration_graph(count):
# =============================================================================
#     if count*TIME_PERIOD/1000 <= DISPLAY_RANGE:
#         start = 0
#         end = int(count*TIME_PERIOD/1000*SAMPLING_RATE)
#     else:
#         start = int((count*TIME_PERIOD/1000 - DISPLAY_RANGE)*SAMPLING_RATE)
#         end = int(count*TIME_PERIOD/1000*SAMPLING_RATE)
#         if end >= len(rawdata.index):
#             end = len(rawdata.index) -1
# =============================================================================
    end = len(db.rawdata.index)-1
    start = end - DISPLAY_RANGE*SAMPLING_RATE
    if start < 0:
        start = 0
    
    graph_data = db.rawdata[start:end]

    if start != end and len(graph_data.index) < DISPLAY_RANGE*SAMPLING_RATE:
        diff = DISPLAY_RANGE*SAMPLING_RATE-graph_data.shape[0]
        diff_range = pd.date_range(end=graph_data.iloc[0, 0],
                                   periods=diff,
                                   freq=str(int(1000/SAMPLING_RATE))+'L')
        diff_df = pd.DataFrame(data={graph_data.columns[0]: diff_range.values, 
                                     graph_data.columns[1]: [None] * diff_range.shape[0], 
                                     graph_data.columns[2]: [None] * diff_range.shape[0], 
                                     graph_data.columns[3]: [None] * diff_range.shape[0]})
        
        graph_data = pd.concat([diff_df, graph_data])
     

    
    
    return Visualizer.acc_grapher(graph_data,return_fig=True)
    

if __name__ == '__main__':
    app.run_server()
    
    
    
    
    
    
    
    