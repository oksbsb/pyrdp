'''
@author: sylvain
'''

import sys, os
# Change path so we find rdpy
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from rdpy.protocol.rdp import rdp

class TestServerFactory(rdp.ServerFactory):
    def startedConnecting(self, connector):
        pass
    
    def clientConnectionLost(self, connector, reason):
        pass
        
    def clientConnectionFailed(self, connector, reason):
        pass

if __name__ == '__main__':
    from twisted.internet import reactor
    reactor.listenTCP(33389, TestServerFactory())
    reactor.run()