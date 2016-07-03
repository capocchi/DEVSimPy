import plotly.plotly as py
import plotly.graph_objs as go
import datetime 
import time 
import numpy as np   

#py.sign_in('cebeka', '475knde90n') #username, apikey
#stream_id = 'rrbzcid5ty' # token
py.sign_in('adrienPlotly', '2vzts6z07f')
stream_id = 'u3pvpjla4o'
stream1 = go.Stream(token=stream_id, maxpoints=60)
plotUrl = py.plot(go.Data([go.Scatter(x=[], y=[], stream=stream1)]), filename="test", auto_open=False, sharing='public', fileopt='new')
print(plotUrl)
s = py.Stream(stream_id)
s.open() # Open the stream
 
i = 0    # a counter
k = 5    # some shape parameter
n = 0
# Delay start of stream by 5 sec (time to switch tabs)
time.sleep(5)
 
while True:
    # Current time on x-axis, random numbers on y-axis
    x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    y = (np.cos(k*i/50.)*np.cos(i/50.)+np.random.randn(1))[0] 
    # Send data to your plot
    s.write(dict(x=x, y=y))  
    print(n)
    n = n+1
    #     Write numbers to stream to append current data on plot,
    #     write lists to overwrite existing data on plot        
    time.sleep(1)  # plot a point every second    
# Close the stream when done plotting
s.close() 