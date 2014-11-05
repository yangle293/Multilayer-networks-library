"""Functions taking in networks and returning transformed versions of them.
"""
from net import *
import math
import itertools

def aggregate(net,aspects,newNet=None,selfEdges=False):
    """Reduces the number of aspects by aggregating them.

    This function aggregates edges from multilayer aspects together
    by summing their weights. Any number of aspects is allowed, and the
    network can have non-diagonal inter-layer links. The layers cannnot 
    be weighted such that they would have different coefficients when 
    the weights are summed together.

    Note that no self-links are created and all the inter-layer links
    are disregarded.

    Parameters
    ----------
    net : MultilayerNetwork
       The original network.
    aspects : int or tuple 
       The aspect which is aggregated over,or a tuple if many aspects
    newNet : MultilayerNetwork 
       Empty network to be filled and returned. If None, a new one is 
       created by this function.
    selfEdges : bool 
       If true aggregates self-edges too

    Returns
    -------
    net : MultiplexNetwork
       A new instance of multiplex network which is produced.

    Examples
    --------
    Aggregating the network with a singe aspect can be done as follows:

    >>> n=net.MultiplexNetwork([('categorical',1.0)])
    >>> an=transforms.aggregate(n,1)

    You need to choose which aspect(s) to aggregate over if the network 
    has multiple aspects:

    >>> n=MultiplexNetwork([2*('categorical',1.0)])
    >>> an1=transforms.aggregate(n,1)
    >>> an2=transforms.aggregate(n,2)
    >>> an12=transforms.aggregate(n,(1,2))
    """
    try:
        aspects=int(aspects)
        aspects=(aspects,)
    except TypeError:
        pass
    
    if newNet==None:
        newNet=MultilayerNetwork(aspects=net.aspects-len(aspects),
                                 noEdge=net.noEdge,
                                 directed=net.directed,
                                 fullyInterconnected=net.fullyInterconnected)
    assert newNet.aspects==net.aspects-len(aspects)
    for d in aspects:
        assert 0<d<=(net.aspects+1)

    #Add nodes
    for node in net:
        newNet.add_node(node)
    
    #Add edges
    edgeIndices=filter(lambda x:math.floor(x/2) not in aspects,range(2*(net.aspects+1)))
    for edge in net.edges:
        newEdge=[]
        for index in edgeIndices:
            newEdge.append(edge[index])
        if selfEdges or not newEdge[0::2]==newEdge[1::2]:
            newNet[tuple(newEdge)]=newNet[tuple(newEdge)]+edge[-1]

    #Add node-layer tuples (if not node-aligned)
    if not net.fullyInterconnected and newNet.aspects>0:
        nodeIndices=filter(lambda x:x not in aspects,range(1,net.aspects+1))
        for nlt in net.iter_node_layers():
            newlayer=[]
            for a in nodeIndices:
                newlayer.append(nlt[a])
            #we need to use the public interface for adding nodes which means that
            #layers are only given as tuples for multi-aspect networks
            if len(newlayer)==1: 
                newNet.add_node(nlt[0],layer=newlayer[0])
            else:
                newNet.add_node(nlt[0],layer=newlayer)

    return newNet


def overlay_network(net):
    """Returns the overlay network of a multilayer network with 1 aspect.

    Returns
    -------
    net : MultiplexNetwork
       A new instance of multiplex network which is produced.
    """
    assert net.aspects==1
    newnet=MultilayerNetwork()
    for layer in net.slices[1]:
        for node1 in net.slices[0]:
            for node2 in net.slices[0]:
                if net.directed or node1>node2:
                    newnet[node1,node2]=newnet[node1,node2]+net[node1,node2,layer,layer]
    return newnet

def subnet(net,nodes,*layers):
    """Returns an induced subgraph with given set of nodes and layers.

    Parameters
    ----------
    net: The original network.
    nodes : sequence
        The nodes that span the induces subgraph.
    *layers : *sequence
        Layers included in the subgraph. One parameter for each aspect.

    Return
    ------
    subnet : type(net)
        The induced subgraph that contains only nodes given in
        `nodes` and the edges between those nodes that are
        present in `net`. Node properties etc are left untouched.
    """
    newNet=None
    if newNet==None:
        if type(net)==MultilayerNetwork:
            newNet=MultilayerNetwork(aspects=net.aspects,
                                     noEdge=net.noEdge,
                                     directed=net.directed)
            raise Exception("Not implemented yet.")
        elif type(net)==MultiplexNetwork:
            newNet=MultiplexNetwork(couplings=net.couplings,
                                           directed=net.directed,
                                           noEdge=net.noEdge,
                                           fullyInterconnected=net.fullyInterconnected)

            #Go through all the combinations of new layers
            for layer in itertools.product(*layers):
                degsum=0
                for node in nodes:        
                    degsum += net[(node,)+layer].deg()
                    newNet.add_node(node)

                if degsum >= len(nodes)*(len(nodes)-1)/2:
                    othernodes=set(nodes)
                    for node in nodes:
                        if not net.directed:
                            othernodes.remove(node)
                        for othernode in othernodes:
                            if net[(node,othernode)+layer]!=net.noEdge:
                                newNet[(node,othernode)+layer]=net[(node,othernode)+layer]
                else:
                    for node in nodes:
                        for neigh in itertools.imap(lambda x:x[0],net[(node,COLON)+layer]):
                            if neigh in nodes:
                                newNet[(node,neigh)+layer]=net[(node,neigh)+layer]

    return newNet


def supra_adjacency_matrix(net,includeCouplings=True):
    """Returns the supra-adjacency matrix and a list of node-layer pairs.

    Parameters
    ----------
    includeCoupings : bool
       If True, the inter-layer edges are included, if False, only intra-layer
       edges are included.

    Returns
    -------
    matrix, nodes : numpy.matrix, list
       The supra-adjacency matrix and the list of node-layer pairs. The order
       of the elements in the list and the supra-adjacency matrix are the same.
    """

    return net.get_supra_adjacency_matrix(includeCouplings=includeCouplings)

def relabel(net,nodeNames=None,layerNames=None):
    """Returns a copy of the network with nodes and layers relabeled.
    
     Parameters
     ----------
     net : MultilayerNetwork, or MultiplexNetwork 
        The original network.
     nodeNames : None, or dict
        The map from node names to node indices.
     layersNames : dict, or sequence of dicts
        The map(s) from (elementary) layer names to (elementary) layer indices.

     Return
     ------
     newnet : type(net)
         The normalized network.
    """
    def dget(d,e):
        if e in d:
            return d[e]
        else:
            return e

    def layer_to_indexlayer(layer,layerNames):
        return tuple([dget(layerNames[i],elayer) for i,elayer in enumerate(layer)])

    if nodeNames==None:
        nodeNames={}

    if net.aspects==1:
        if isinstance(layerNames,dict):
            layerNames=[layerNames]

    for aspect in range(net.aspects):
        if len(layerNames)<aspect+1:
            layerNames.append({})
     
    if type(net)==MultilayerNetwork:
        newNet=MultilayerNetwork(aspects=net.aspects,
                                 noEdge=net.noEdge,
                                 directed=net.directed,
                                 fullyInterconnected=net.fullyInterconnected)
    elif type(net)==MultiplexNetwork:
            newNet=MultiplexNetwork(couplings=net.couplings,
                                    directed=net.directed,
                                    noEdge=net.noEdge,
                                    fullyInterconnected=net.fullyInterconnected)

    for node in net:
        newNet.add_node(dget(nodeNames,node))
    for aspect in range(net.aspects):
        for layer in net.slices[aspect+1]:
            newNet.add_layer(dget(layerNames[aspect],layer),aspect=aspect+1) 

    if not net.fullyInterconnected:
        for nodelayer in net.iter_node_layers():
            layer=layer_to_indexlayer(nodelayer[1:],layerNames)
            if net.aspects==1:
                layer=layer[0]
            newNet.add_node(dget(nodeNames,nodelayer[0]),layer=layer)

    if type(net)==MultilayerNetwork:
        raise Exception("Not implemented yet.")
    elif type(net)==MultiplexNetwork:
            for layer in net.iter_layers():
                if net.aspects==1:
                    layertuple=(layer,)
                else:
                    layertuple=layer
                for node in net.A[layer]:
                    for neigh in net.A[layer][node]:
                        newNet[(dget(nodeNames,node),dget(nodeNames,neigh))+layer_to_indexlayer(layertuple,layerNames)]=net[(node,neigh)+layertuple]

                            
    return newNet

def normalize(net,nodesToIndices=None,layersToIndices=None,nodeStart=0,layerStart=0):
    """Returns a copy of the network with layer and node indices as integers.

    In network with n nodes the nodes are renamed so that they run from 0 to n-1.
    In network has b_a elementary layers in aspect a, the layers are renamed so 
    that they run from 0 to b_a-1.

    Parameters
    ----------
    net : MultilayerNetwork, or MultiplexNetwork 
       The original network.
    nodesToIndices : None, or bool
       True returns the map from node names to node indices, False returns the map from 
       node indices to node names, and None doesn't return anything.
    layersToIndices : None, or bool
       True returns the map(s) from (elementary) layer names to (elementary) layer indices,
       False returns the map(s) from (elementary) layer indices to (elementary) layer names,
       and None doesn't return anything.
    nodeStart : int
       The indexing for nodes starts from this value.
    layerStart : int
       The indexing for layers starts from this value.

    Return
    ------
    newnet : type(net)
        The normalized network.
    (optional) nodeNames : dict
        The map from node names/indices to node indices/names.
    (optional) layerNames : dict, or list of dicts
        The map(s) from (elementary) layer names/indices to (elementary) layer indices/names. One
        map for each aspect.
    """
  
    nodeNames={}
    layerNames=[{} for aspect in range(net.aspects)]

    for i,node in enumerate(sorted(net)):
        nodeNames[node]=i+nodeStart
    for aspect in range(net.aspects):
        for i,layer in enumerate(sorted(net.slices[aspect+1])):
            layerNames[aspect][layer]=i+layerStart

    newNet=relabel(net,nodeNames=nodeNames,layerNames=layerNames)

    if nodesToIndices==False:
        indicesToNodes={}
        for node,index in nodeNames.iteritems():
            indicesToNodes[index]=node
        nodeNames=indicesToNodes

    if layersToIndices==False:
        for aspect in range(net.aspects):
            indicesToLayers={}
            for layer,index in layerNames[aspect].iteritems():
                indicesToLayers[index]=layer
            layerNames[aspect]=indicesToLayers

    if net.aspects==1:
        layerNames=layerNames[0]

    if nodesToIndices==None and layersToIndices==None:
        return newNet
    elif nodesToIndices!=None and layersToIndices==None:
        return newNet,nodeNames
    elif nodesToIndices==None and layersToIndices!=None:
        return newNet,layerNames
    elif nodesToIndices!=None and layersToIndices!=None:
        return newNet,nodeNames,layerNames
