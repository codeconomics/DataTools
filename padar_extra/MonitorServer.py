from websocket_server import WebsocketServer
import asyncio
import pandas as pd
import logging

count = 0
refresh=12.5
sampling_rate=80
feature_time = 12.8

featuredata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/Derived/Preprocessed/2015/10/08/14/ActigraphGT9X-PostureAndActivity-NA.TAS1E23150066-PostureAndActivity.2015-10-08-14-00-00-000-M0400.feature.csv')
featuredata = featuredata.values.tolist()
featuredata.sort(key=lambda x: x[1])

annotationdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/Derived/Preprocessed/2015/10/08/14/SPADESInLab.alvin-SPADESInLab.2015-10-08-14-10-41-252-M0400.class.csv')
annotationdata = annotationdata.values.tolist()
annotationdata.sort(key=lambda x: x[1])

accdata = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2/Derived/Preprocessed/2015/10/08/14/ActigraphGT9X-AccelerationCalibrated-NA.TAS1E23150066-AccelerationCalibrated.2015-10-08-14-00-00-000-M0400.sensor.csv')
print('1')

async def producer():
    asyncio.sleep(refresh/1000)

    global count

    feature_update = []
    annotation_update = []
    acc_update = accdata[int(count*refresh/1000*sampling_rate):
        int((count+1)*refresh/1000*sampling_rate)]
    currtime = pd.to_datetime(acc_update.iloc[-1,0])
    
    annotation_update = []
    while currtime >= pd.to_datetime(annotationdata[0][1]):
        annotation_update.append(annotationdata.pop(0))
        feature_update.append(featuredata.pop(0))

    message = dict(acc_update=acc_update.values.tolist(), 
                feature_update=feature_update, 
                annotation_update=annotation_update)
    count += 1

    return message

if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    server = WebsocketServer()
    test_producer = {
        'func': producer,
        'desc': "This producer generates pseudo streamming data every fresh rate"
    }
    print('2')
    server.make_producer(producer=test_producer).start()



    

    


