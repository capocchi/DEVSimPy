import urllib
import json

class ElevationRequest:


    ELEVATION_BASE_URL = 'http://maps.googleapis.com/maps/api/elevation/json'

    def __init__(self):
        pass



    def getElevationFromPoint(self, point, sensor='false'):
        elvtn_args=({
                    'locations': self.convertPointToStr(point),
                    'sensor': sensor
                    })
        url = self.ELEVATION_BASE_URL + '?' + urllib.urlencode(elvtn_args)
        response = json.load(urllib.urlopen(url))
        print resdponse['results']
        return response['results'][0]['elevation']



    def getElevationFromLine(self, start, end, samples=100, sensor='false'):
        elvtn_args = ({
                    'path': self.convertPointToStr(start) + "|" + self.convertPointToStr(end),
                    'samples': samples,
                    'sensor':sensor
                    })

        url = self.ELEVATION_BASE_URL + '?' + urllib.urlencode(elvtn_args)
        response = json.load(urllib.urlopen(url))

        elevationArray = []
        for resultset in response['results']:
            elevationArray.append(resultset['elevation'])
        return elevationArray

#-------------INTERNAL FUNCTIONS--------------#

    def convertPointToStr(self,point):
        return str(point[0]) + "," + str(point[1])


#--------------------TEST---------------------#

#myER =  ElevationRequest()
#print myER.getElevationFromPoint((12,12))
#print myER.getElevationFromLine((12,12),(13,13),10)