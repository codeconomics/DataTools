#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 10:52:06 2018

@author: zhangzhanming
"""
import pandas as pd
import time
import threading 

class AccDataBase(object):
    def __init__(self, monitor=None):
        self.monitor = monitor
        self.featuredata = pd.DataFrame()
        self.annotationdata = pd.DataFrame()
        self.rawdata = pd.DataFrame()
    
    
    def set_data_set(self, featuredata=None, annotationdata=None, rawdata=None):
        if isinstance(featuredata, str): 
            self.featuredata = pd.read_csv(featuredata)
        if isinstance(annotationdata, str): 
            self.annotationdata = pd.read_csv(annotationdata)
        if isinstance(rawdata, str): 
            self.rawdata = pd.read_csv(rawdata)
        
        if isinstance(featuredata, pd.DataFrame):
            self.featuredata = featuredata
        if isinstance(annotationdata, pd.DataFrame):
            self.annotationdata = annotationdata
        if isinstance(rawdata, pd.DataFrame):
            self.rawdata = rawdata

    
    def set_monitor(self, monitor):
        self.monitor = monitor
    
    def update(self, feature_update=None, annotation_update=None,
               raw_update=None):
        self.__append_data(feature_update, annotation_update, raw_update)
# =============================================================================
#         self.__delete_data(feature_update is not None, 
#                            annotation_update is not None,
#                            raw_update is not None)
# =============================================================================
        
        
    def __append_data(self, feature_update, annotation_update, raw_update):
        if feature_update is not None:
            if len(self.featuredata.index) == 0:
                self.featuredata = feature_update
            self.featuredata = pd.concat([self.featuredata, feature_update])
            
        if annotation_update is not None:
            if len(self.annotationdata.index) == 0:
                self.annotationdata = annotation_update
            self.annotationdata = pd.concat([self.annotationdata, annotation_update])
            
        if raw_update is not None:
            if len(self.rawdata.index) == 0:
                self.rawdata = raw_update
            self.rawdata = pd.concat([self.rawdata, raw_update])
 
           
    def __delete_data(self, update_feature, update_annotation, update_raw):
        if update_feature:
            if len(self.featuredata.index):
                pass


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self.count = 0
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(self.count, *self.args, **self.kwargs)
        self.count += 1

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
        self._timer.start()
        self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
                    
        
        
class Monitor(object):
    def __init__(self, refresh=12.5, sampling_rate=80, test=True):
        self.__observers = []
        self.refresh = refresh
        self.sampling_rate = sampling_rate
        self.test = test
        
        
    def register_observer(self, observer):
        self.__observers.append(observer)
    
    
    def notify_observers(self, feature_update=None, annotation_update=None,
               raw_update=None):
        for observer in self.__observers:
            observer.update(feature_update=feature_update, 
                            annotation_update=annotation_update,
                            raw_update=raw_update)
            
        
    def listen(self):
        if self.test:
            #self.featuredata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/Derived/Preprocessed/2015/10/08/14/ActigraphGT9X-PostureAndActivity-NA.TAS1E23150066-PostureAndActivity.2015-10-08-14-00-00-000-M0400.feature.csv')
            #self.annotationdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/MasterSynced/2015/10/08/14/SPADESInLab.alvin-SPADESInLab.2015-10-08-14-10-41-252-M0400.annotation.csv')
            rawdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/MasterSynced/2015/10/08/14/ActigraphGT9X-AccelerationCalibrated-NA.TAS1E23150066-AccelerationCalibrated.2015-10-08-14-00-00-000-M0400.sensor.csv')
            
            def __get_new_data(count, refresh, sampling_rate, rawdata):
                raw_update = rawdata[int(count*refresh/1000*sampling_rate):
                    int((count+1)*refresh/1000*sampling_rate)]
                self.notify_observers(raw_update = raw_update)
            
            rt = RepeatedTimer(self.refresh/1000, __get_new_data, self.refresh,
                              self.sampling_rate, rawdata)
            

if __name__ == '__main__':
    monitor = Monitor()
    db = AccDataBase(monitor)
    monitor.register_observer(db)
    monitor.listen()
        
        
    
    
    