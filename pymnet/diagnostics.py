from net import *

def degs(net):
    """Returns the degree distribution of a multilayer network.
    """
    degs={}
    for node in net:
        d=net[node].deg()
        degs[d]=degs.get(d,0)+1
    return degs

def density(net):
    """Returns the density of the network.

    Density is defined as the number of edges in the network divided by the number
    of possible edges in a general multilayer network with the same set of nodes and
    layers.
    """
    if len(net)==0:
        return 0

    if net.fullyInterconnected:        
        nl=len(net.get_layers(0))
        for a in range(net.aspects):
            nl=nl*len(net.get_layers(a+1))
        if net.directed:
            pedges=nl*(nl-1)
        else:
            pedges=(nl*(nl-1))/2
            
    return len(net.edges)/float(pedges)


def multiplex_density(net):
    """Returns a dictionary of densities of each intra-layer network of a multiplex network.
    """
    assert isinstance(net,MultiplexNetwork)
    d={}
    for layer in net.iter_layers():
        d[layer]=density(net.A[layer])
    return d

def multiplex_degs(net):
    """Returns a dictionary of degree distributions of each intra-layer network of a multiplex network.
    """
    assert isinstance(net,MultiplexNetwork)
    
    d={}
    for layer in net.iter_layers():
        d[layer]=degs(net.A[layer])
    return d