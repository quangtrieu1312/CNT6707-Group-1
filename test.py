#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSBridge
from mininet.cli import CLI
from mininet.log import setLogLevel
import subprocess

class MyTopo(Topo):
    def build(self):
        client = self.addHost('C', ip='192.168.0.2/24', defaultRoute='via 192.168.0.1')
        server = self.addHost('S', ip='192.168.1.2/24', defaultRoute='via 192.168.1.1')
        clientRouter = self.addHost('CR', ip='192.168.0.1/24')
        serverRouter = self.addHost('SR', ip='192.168.1.1/24')
        self.addLink(client, clientRouter, intfName1='eth0', intfName2='eth0')
        self.addLink(server, serverRouter, intfName1='eth0', intfName2='eth0')
        self.addLink(clientRouter, serverRouter, intfName1='eth1', intfName2='eth1', params1={'ip':'10.1.1.1/24'}, params2={'ip':'10.1.1.2/24'})
        self.addLink(clientRouter, serverRouter, intfName1='eth2', intfName2='eth2', params1={'ip':'10.1.2.1/24'}, params2={'ip':'10.1.2.2/24'})

if __name__ == '__main__':
    setLogLevel('info')
    print('Loading topology')
    net = Mininet(topo=MyTopo(), link=TCLink,
                  switch=OVSBridge, controller=None)
    net.start()
    print('Setting up extra config')
    client, server = net.get('C', 'S')
    clientRouter, serverRouter = net.get('CR', 'SR')
    clientRouter.cmd('nft flush ruleset')
    clientRouter.cmd('nft add table ip spray')
    clientRouter.cmd('nft add chain ip spray pre \'{ type filter hook prerouting priority mangle; }\'')
    clientRouter.cmd('nft add rule ip spray pre iifname "eth0" meta mark set numgen inc mod 2 offset 1')
    clientRouter.cmd('nft add chain ip spray forward \'{ type filter hook forward priority mangle; }\'')
    clientRouter.cmd('nft add rule ip spray forward meta mark 1 counter')
    clientRouter.cmd('nft add rule ip spray forward oifname "eth1" counter')
    clientRouter.cmd('nft add rule ip spray forward meta mark 2 counter')
    clientRouter.cmd('nft add rule ip spray forward oifname "eth2" counter')
    clientRouter.cmd('ip rule del table 101')
    clientRouter.cmd('ip route flush table 101')
    clientRouter.cmd('ip rule add fwmark 1 table 101')
    clientRouter.cmd('ip route add default via 10.1.1.2 dev eth1 table 101')
    clientRouter.cmd('ip rule del table 102')
    clientRouter.cmd('ip route flush table 102')
    clientRouter.cmd('ip rule add fwmark 2 table 102')
    clientRouter.cmd('ip route add default via 10.1.2.2 dev eth2 table 102')
    
    clientRouter.cmd('for interface in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 0 >$interface; done')
    clientRouter.cmd('for interface in /proc/sys/net/ipv6/conf/*/disable_ipv6; do echo 1 >$interface; done')
    clientRouter.cmd('sysctl -w net.ipv4.ip_forward=1')
    
    serverRouter.cmd('ip route add default via 10.1.2.1')

    serverRouter.cmd('for interface in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 0 >$interface; done')
    serverRouter.cmd('for interface in /proc/sys/net/ipv6/conf/*/disable_ipv6; do echo 1 >$interface; done')
    serverRouter.cmd('sysctl -w net.ipv4.ip_forward=1')
    #print('Info dump client')
    #print(client.cmd('ip a; ip route show'))
    #print('Info dump client router')
    #print(clientRouter.cmd('ip a; ip route show; ip route get 192.168.0.2; ip route get 192.168.1.2'))
    #print('Info dump server router')
    #print(serverRouter.cmd('ip a; ip route show; ip route get 192.168.0.2; ip route get 192.168.1.2'))
    #print('Info dump server')
    #print(server.cmd('ip a; ip route show; ip route get 192.168.0.2'))
    print('Sanity check')
    print(client.cmd('ping -i 0.02 192.168.1.2 -c100'))
    print(clientRouter.cmd('ip -s link show dev eth1'))
    print(clientRouter.cmd('ip -s link show dev eth2'))
    print(clientRouter.cmd('nft list ruleset'))
    print('Test begin')
    CLI(net)
    net.stop()
