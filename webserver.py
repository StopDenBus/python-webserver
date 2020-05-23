#!/usr/bin/python3

from twisted.web import server, resource
from twisted.internet import reactor, defer
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from pprint import pprint
import base64
import json
import os
import sys
from pathlib import Path

class DummyServer(resource.Resource):

    isLeaf = True

    workDir = Path().absolute()

    http_requests_total = 0

    def listing(self, request):

        directory = request.uri.decode()

        html = "<br>"

        toplevel_directory = "/".join(directory.split('/')[0:-2])

        directory = "{}/{}".format(self.workDir, directory)        

        html += '<a href="{}/">..</a><br>'.format(toplevel_directory)

        try:

            p = Path(directory)

        except: 
            
            return html
        
        for entry in os.scandir(p):
            
            if entry.is_dir():
                
                html += '<a href="{}/">{}</a><br>'.format(entry.name, entry.name)

        return html

    def getAccessLog(self, request):

        access_log = { 'request': request.uri.decode(), 'method': request.method.decode(), 'client': request.getClientAddress().host }
            
        access_log['hostname'] = request.getRequestHostname().decode()
            
        access_log['type'] = 'access_log'

        return access_log

    def incrementMetrics(self, result):

        metrics_host = "http://{}/metrics".format(os.environ['METRIC_HOST'])

        print(metrics_host)

        agent = Agent(reactor)

        agent.request(
            b'POST',
            metrics_host.encode(),
            Headers( { 'Content-Type': ['application/json'] } ),
            None )

        return


    def render_GET(self, request):        

        #d = defer.Deferred()

        #d.addCallback(self.incrementMetrics)

        #d.callback("")

        html = "<html>"        
    
        html += "Listing of {}".format(request.uri.decode())

        try:
            
            html += self.listing(request)

            # print access log
            print(json.dumps(self.getAccessLog(request)))

            request.setResponseCode(200)

        except:

            html += "Forbidden"

            error_log = {}

            error_log['request'] = request.uri.decode()

            error_log['method'] = request.method.decode()

            error_log['client'] = request.getClientAddress().host
            
            error_log['hostname'] = request.getRequestHostname().decode()
            
            error_log['type'] = 'error_log'

            print(json.dumps(error_log))

            request.setResponseCode(403)
        
        html += "</html>"

        request.setHeader("Content-Type", "text/html; charset=utf-8")
        
        return html.encode('utf-8')

s = server.Site(DummyServer())

reactor.listenTCP(8080, s)

reactor.run()
