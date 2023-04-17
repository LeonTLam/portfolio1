'''

DATA 2410: Mininet script to produce a network like the following:

                                          +-------+          +-------+                                                             
                                          |       |          |       |                                                             
+-------+                                 |   H7  |          |   H8  |            +-------+                                        
|       |                                 +-------+          +-------+            |       |                                        
|   H1  |-\                                   |                  |              --|  H4   |                                        
+-------+  -\                                 |                  |            -/  +-------+                                        
             -\                               |                  |          -/                                                     
               -\                             |                  |        -/                                                       
+-------+        -\  +-------+            +-------+          +-------+  -/        +-------+                                        
|       |          - |       |     L1     |       |    L2    |       |-/          |       |                                        
|   H2  |------------|  R1   |------------|   R2  |----------|    R3 |-------------   H5  |                                        
+-------+         -/ +-------+            +-------+          +--------\           +-------+                                        
                -/                                               |     -\                                                          
              -/-                                                |       -\                                                        
+-------+   -/                                                L3 |         -\     +-------+                                        
|       | -/                                                     |           -\   |  H6   |                                        
|  H3   |/                                                   +-------+         -- |       |                                        
+-------+                                                    |   R4  |            +-------+                                        
                                                             |       |                                                            -
                                                             +-------+                                                             
                                                                 |                                                                 
                                                                 |                                                                 
                                                                 |                                                                 
                                                                 |                                                                 
                                                             +-------+                                                             
                                                             |       |                                                             
                                                             |  H9   |                                                             
                                                             +-------+                                                             



'''


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink


class LinuxRouter( Node ):
    """A Node with IP forwarding enabled.
    Means that every packet that is in this node, comunicate freely with its interfaces."""

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()



class PortfolioNetwork2410( Topo ):

    def build( self, **_opts ):
        #subnet A with three hosts (h1, h2, and h3), a switch, and a router (r1)
        h1=self.addHost("h1",ip="10.0.0.2/24", defaultRoute='via 10.0.0.1')
        h2=self.addHost("h2",ip="10.0.0.3/24", defaultRoute='via 10.0.0.1')
        h3=self.addHost("h3",ip="10.0.0.4/24", defaultRoute='via 10.0.0.1')
        s1 = self.addSwitch("s1")         
        r1=self.addNode("r1",cls=LinuxRouter,ip='10.0.0.1/24', defaultRoute='via 10.0.1.2')
        for h in (h1,h2,h3):
            self.addLink(h,s1)
        self.addLink(s1,r1,intfName2='r1-eth0',params2={ 'ip' : '10.0.0.1/24' })#,max_queue_size=834, use_htb=True)
        
        #subnet B - r1 - r2
        
        r2=self.addNode("r2",cls=LinuxRouter,ip='10.0.1.2/24') 
        self.addLink(r1,r2,intfName1='r1-eth1', params1={ 'ip' : '10.0.1.1/24' }, bw=40, delay='10ms', max_queue_size=67, use_htb=True)#,max_queue_size=834, use_htb=True)
        
        
        #subnet C  r2 - h7
        h7=self.addHost("h7",ip="10.0.2.2/24", defaultRoute='via 10.0.2.1')
        self.addLink(r2,h7,intfName1='r2-eth1', params1={ 'ip' : '10.0.2.1/24' })#,max_queue_size=834, use_htb=True)



        #subnet D  r2 - r3
        r3=self.addNode("r3",cls=LinuxRouter,ip='10.0.3.2/24') 
        self.addLink(r2,r3,intfName1='r2-eth2', params1={ 'ip' : '10.0.3.1/24' }, bw=30, delay='20ms', max_queue_size=100, use_htb=True)#,max_queue_size=834, use_htb=True)
        
	
	    #subnet    r3  - H8
        h8=self.addHost("h8",ip="10.0.4.2/24", defaultRoute='via 10.0.4.1')
        self.addLink(r3,h8,intfName1='r3-eth1', params1={ 'ip' : '10.0.4.1/24' })#,max_queue_size=834, use_htb=True)

	
    	# subnet E  r3 - H4-H7
        h4=self.addHost("h4",ip="10.0.5.2/24", defaultRoute='via 10.0.5.1')
        h5=self.addHost("h5",ip="10.0.5.3/24", defaultRoute='via 10.0.5.1')
        h6=self.addHost("h6",ip="10.0.5.4/24", defaultRoute='via 10.0.5.1')
        s2 = self.addSwitch("s2")         
        for h in (h4,h5,h6):
            self.addLink(h,s2)
        self.addLink(s2,r3,intfName2='r3-eth2',params2={ 'ip' : '10.0.5.1/24' })#,max_queue_size=834, use_htb=True)
	
	
	
	    # subnet G r3 - r4

        r4=self.addNode("r4",cls=LinuxRouter,ip='10.0.6.2/24', defaultRoute='via 10.0.6.1') 
        self.addLink(r3,r4,intfName1='r3-eth3', params1={ 'ip' : '10.0.6.1/24' }, bw=20, delay='10ms', max_queue_size=33, use_htb=True)#,max_queue_size=834, use_htb=True)
        
	
	    #subnet I: r4 - H9
        h9=self.addHost("h9",ip="10.0.7.2/24", defaultRoute='via 10.0.7.1')
        self.addLink(r4,h9,intfName1='r4-eth1', params1={ 'ip' : '10.0.7.1/24' })#,max_queue_size=834, use_htb=True)



topo = PortfolioNetwork2410()
net = Mininet( topo=topo, link=TCLink )
net.start()

#ip route add ipA via ipB dev INTERFACE
#every packet going to ipA must first go to ipB using INTERFACE
net["r2"].cmd("ip route add 10.0.0.0/24 via 10.0.1.1 dev r2-eth0")
net["r2"].cmd("ip route add 10.0.4.0/24 via 10.0.3.2 dev r2-eth2")
net["r2"].cmd("ip route add 10.0.5.0/24 via 10.0.3.2 dev r2-eth2")
net["r2"].cmd("ip route add 10.0.6.0/24 via 10.0.3.2 dev r2-eth2")
net["r2"].cmd("ip route add 10.0.7.0/24 via 10.0.3.2 dev r2-eth2")

net["r3"].cmd("ip route add 10.0.0.0/24 via 10.0.3.1 dev r3-eth0")
net["r3"].cmd("ip route add 10.0.1.0/24 via 10.0.3.1 dev r3-eth0")
net["r3"].cmd("ip route add 10.0.2.0/24 via 10.0.3.1 dev r3-eth0")
net["r3"].cmd("ip route add 10.0.7.0/24 via 10.0.6.2 dev r3-eth3")


net["r1"].cmd("ethtool -K r1-eth1 tso off")
net["r1"].cmd("ethtool -K r1-eth1 gso off")
net["r1"].cmd("ethtool -K r1-eth1 lro off")
net["r1"].cmd("ethtool -K r1-eth1 gro off")
net["r1"].cmd("ethtool -K r1-eth1 ufo off")


net["r2"].cmd("ethtool -K r2-eth2 tso off")
net["r2"].cmd("ethtool -K r2-eth2 gso off")
net["r2"].cmd("ethtool -K r2-eth2 lro off")
net["r2"].cmd("ethtool -K r2-eth2 gro off")
net["r2"].cmd("ethtool -K r2-eth2 ufo off")


net["r3"].cmd("ethtool -K r3-eth3 tso off")
net["r3"].cmd("ethtool -K r3-eth3 gso off")
net["r3"].cmd("ethtool -K r3-eth3 lro off")
net["r3"].cmd("ethtool -K r3-eth3 gro off")
net["r3"].cmd("ethtool -K r3-eth3 ufo off")

for i in range (1,10,1):
    node = "h" + str(i)
    iface = node + "-eth0" 
    net[node].cmd("ethtool -K " + iface + " tso off")
    net[node].cmd("ethtool -K " + iface + " gso off")
    net[node].cmd("ethtool -K " + iface + " lro off")
    net[node].cmd("ethtool -K " + iface + " gro off")
    net[node].cmd("ethtool -K " + iface + " ufo off")



net.pingAll()
CLI( net )
net.stop()