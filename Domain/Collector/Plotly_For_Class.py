# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          Plotly_For_Class.py
 Model:         Plot classification results as a graph for plot.ly (https://plot.ly/)
 Authors:       C. Kessler
 Organization:  UMR CNRS 6134
 Date:          17/06/2016
 License:       GPL V3.0
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import chart_studio.plotly as py
import plotly.graph_objects as go

    
### Model class ----------------------------------------------------------------
class Plotly_For_Class(DomainBehavior):
    ''' DEVS Class for Plotly_For_Class model
    '''

    def __init__(self, key='', username='', plotUrl='',
                sharing=['public', 'private', 'secret'],
                fileopt = ['new', 'overwrite', 'extend', 'append']):
        ''' Constructor.

            fn (string) -- the name that will be associated with this figure
            fileopt ('new' | 'overwrite' | 'extend' | 'append') -- 'new' creates a
                'new': create a new, unique url for this plot
                'overwrite': overwrite the file associated with `filename` with this
                'extend': add additional numbers (data) to existing traces
                'append': add additional traces to existing data lists
            world_readable (default=True) -- make this figure private/public
            auto_open (default=True) -- Toggle browser options
                True: open this plot in a new browser tab
                False: do not open plot in the browser, but do return the unique url
            sharing ('public' | 'private' | 'sharing') -- Toggle who can view this graph
                - 'public': Anyone can view this graph. It will appear in your profile 
                    and can appear in search engines. You do not need to be 
                    logged in to Plotly to view this chart.
                - 'private': Only you can view this plot. It will not appear in the
                    Plotly feed, your profile, or search engines. You must be
                    logged in to Plotly to view this graph. You can privately
                    share this graph with other Plotly users in your online
                    Plotly account and they will need to be logged in to
                    view this plot.
                - 'secret': Anyone with this secret link can view this chart. It will
                    not appear in the Plotly feed, your profile, or search
                    engines. If it is embedded inside a webpage or an IPython
                    notebook, anybody who is viewing that page will be able to
                    view the graph. You do not need to be logged in to view
                    this plot.
        '''
        DomainBehavior.__init__(self)
        
        if key != '' and username != '':
            py.sign_in(username, key)
        self.plotUrl = ''
        self.state = {'status': 'IDLE', 'sigma':INFINITY}

    def extTransition(self):
        ''' DEVS external transition function.
        '''
        msg = self.peek(self.IPorts[0])
        classes = msg.value[0]
        #print('--->')
        #print(classes)

        barsX = []
        barsY = []

        for c in classes:
            barsX.append(c['label'])
            barsY.append(c['score'])
                
        bars = go.Bar(
            x=barsX,
            y=barsY,
            name='Classification'
        )        

        data = [bars]
        layout = go.Layout(
            xaxis=dict(tickangle=-45)
        )

        fig = go.Figure(data=data, layout=layout)
        #py.iplot(fig, filename='angled-text-bar')
                
        self.plotUrl = py.plot(data, filename='class', auto_open=False, fileopt='new')
        print((self.plotUrl))
        
        self.state['sigma'] = 0

    def outputFnc(self):
        ''' DEVS output function.
        '''
        pass

    def intTransition(self):
        ''' DEVS internal transition function.
        '''
        self.state['sigma'] = INFINITY

    def timeAdvance(self):
        ''' DEVS Time Advance function.
        '''
        return self.state['sigma']

    def finish(self, msg):
        ''' Additional function which is lunched just before the end of the simulation.
        '''
        pass
