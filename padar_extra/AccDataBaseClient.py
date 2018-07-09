
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 10:52:06 2018

@author: zhangzhanming
"""

from websocket_client import WebsocketClient
import asyncio
import pandas as pd
import logging
import json
import time
import threading
import datetime
import websockets
import numpy as np

class AccDataBase(object):

    feature_columns = ['START_TIME', 'STOP_TIME', 'MEAN_VM', 'STD_VM', 'MAX_VM', 'DOM_FREQ_VM',
       'DOM_FREQ_POWER_RATIO_VM', 'HIGHEND_FREQ_POWER_RATIO_VM', 'RANGE_VM',
       'ACTIVE_SAMPLE_PERC_VM', 'NUMBER_OF_ACTIVATIONS_VM',
       'ACTIVATION_INTERVAL_VAR_VM', 'MEDIAN_X_ANGLE', 'MEDIAN_Y_ANGLE',
       'MEDIAN_Z_ANGLE', 'RANGE_X_ANGLE', 'RANGE_Y_ANGLE', 'RANGE_Z_ANGLE']
    annotation_columns = ['START_TIME', 'STOP_TIME', 'posture', 'four_classes', 'MDCAS',
            'indoor_outdoor', 'activity', 'activity_intensity', 'hand_gesture']
    acc_columns = ['HEADER_TIME_STAMP','X_ACCELERATION_METERS_PER_SECOND_SQUARED',
        'Y_ACCELERATION_METERS_PER_SECOND_SQUARED',
        'Z_ACCELERATION_METERS_PER_SECOND_SQUARED']
    

    #initialized feature data with column names
    def __init__(self, monitor=None):
        self.monitor = monitor
        self.featuredata = pd.DataFrame(columns = self.feature_columns)
        self.annotationdata = pd.DataFrame(columns = self.annotation_columns)
        self.accdata = pd.DataFrame(columns = self.acc_columns)


    def set_data_set(self, featuredata=None, annotationdata=None, accdata=None):
        if isinstance(featuredata, str):
            self.featuredata = pd.read_csv(featuredata)
        if isinstance(annotationdata, str):
            self.annotationdata = pd.read_csv(annotationdata)
        if isinstance(accdata, str):
            self.accdata = pd.read_csv(accdata)

        if isinstance(featuredata, pd.DataFrame):
            self.featuredata = featuredata
        if isinstance(annotationdata, pd.DataFrame):
            self.annotationdata = annotationdata
        if isinstance(accdata, pd.DataFrame):
            self.accdata = accdata


    def set_monitor(self, monitor):
        self.monitor = monitor


    def update(self, feature_update=None, annotation_update=None,
               acc_update=None):
        self.__append_data(feature_update, annotation_update, acc_update)
        self.__delete_data(feature_update,
                           annotation_update,
                           acc_update)

       
    def __append_data(self, feature_update, annotation_update, acc_update):
        if feature_update is not None:
            self.featuredata = pd.concat([self.featuredata, feature_update]).reset_index(drop=True)

        if annotation_update is not None:
            self.annotationdata = pd.concat([self.annotationdata, annotation_update]).reset_index(drop=True)

        if acc_update is not None:
            self.accdata = pd.concat([self.accdata, acc_update]).reset_index(drop=True)


    def __delete_data(self, update_feature, update_annotation, update_acc):
        store_time = datetime.timedelta(minutes=1)
        if update_feature is not None and pd.to_datetime(self.featuredata.iloc[self.featuredata.shape[0]-1,1])-pd.to_datetime(self.featuredata.iloc[0,0]) > store_time:
            self.featuredata = self.featuredata[pd.to_datetime(self.featuredata.iloc[:,0])>= (pd.to_datetime(self.featuredata.iloc[self.featuredata.shape[0]-1,1])- store_time/2)].reset_index(drop=True)
        if update_annotation is not None and pd.to_datetime(self.annotationdata.iloc[self.annotationdata.shape[0]-1,1])-pd.to_datetime(self.annotationdata.iloc[0,0]) > store_time:
            self.annotationdata = self.annotationdata[pd.to_datetime(self.annotationdata.iloc[:,0])>= (pd.to_datetime(self.annotationdata.iloc[self.annotationdata.shape[0]-1,1])- store_time/2)].reset_index(drop=True)
        if update_acc is not None and (pd.to_datetime(self.accdata.iloc[self.accdata.shape[0]-1,0])-pd.to_datetime(self.accdata.iloc[0,0])) > store_time:
            self.accdata = self.accdata[(pd.to_datetime(self.accdata.iloc[:,0])>= pd.to_datetime(self.accdata.iloc[self.accdata.shape[0]-1,0])- store_time/2)].reset_index(drop=True)

    
    async def consumer(self, message):
        message = json.loads(message)

        message['acc_update'] = np.asarray(message['acc_update'])
        message['annotation_update'] = np.asarray(message['annotation_update'])
        message['feature_update'] = np.asarray(message['feature_update'])

        if len(message['acc_update']) > 0:
            message['acc_update'] = pd.DataFrame(message['acc_update'], columns=self.acc_columns)
        else:
            message['acc_update'] = None
        if len(message['annotation_update']) > 0:
            message['annotation_update'] = pd.DataFrame(message['annotation_update'], columns=self.annotation_columns)
        else:
            message['annotation_update'] = None
        if len(message['feature_update']) > 0:
            message['feature_update'] = pd.DataFrame(message['feature_update'], columns=self.feature_columns)
        else:
            message['feature_update'] = None

        self.update(acc_update = message['acc_update'], 
            feature_update=message['feature_update'], 
            annotation_update=message['annotation_update'])

        self.callback(self)
        
        return 'Got it!'


    def set_callback(self, callback):
        self.callback = callback


    def start_receiving(self, consumer_callback):
        import sys
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        client = WebsocketClient()
        self.set_callback(consumer_callback)
        client.make_consumer(consumer=self.consumer).start()

if __name__ == '__main__':
    import sys
    import time
    db = AccDataBase()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    client = WebsocketClient()
    client.make_consumer(consumer=db.consumer).start()