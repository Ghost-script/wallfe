from flask import g
from flask.ext import restful
 
from wallfe import api
import json
#from serializer import ChannelSerializer, PostSerializer
 

class ChannelView(restful.Resource):
    def get(self,channelname):
        with open('wallfe/database/db.json') as outfile:
            planet = json.loads(outfile.read())
        return planet[channelname][0].keys()
 
class PostView(restful.Resource):
    def get(self, listname):
        with open('wallfe/database/db.json') as outfile:
            planet = json.loads(outfile.read())
        #return PostSerializer(planet[listname][0]['entries'][0]).data

        return planet[listname].keys()

api.add_resource(PostView, '/api/v1/posts/<channelname>/<listname>')
api.add_resource(ChannelView, '/api/v1/channel/<channelname>')