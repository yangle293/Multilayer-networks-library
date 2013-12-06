"""Functions for generating multilayer and multiplex networks using various network models.
"""

from net import MultilayerNetwork,MultiplexNetwork
import math,random

def single_layer_conf(net,degs):
    """Generates a realization of configuration model network.

    Parameters
    ----------
    net : MultilayerNetwork with aspects=0
       Empty network object that is to be filled.
    deg : dict 
       The degree distribution. Keys are degrees, and corresponding
       values are number of nodes with the given degree.

    Notes
    -----
    The algorithm used here is similar to the one in article:
    B.D McKay, N.C Wormald 'Uniform Generation of Random Regular Graphs of Moderate Degree'
    Journal of Algorithms 11, pages 52-67 (1990)

    The difference between the algorithm presented in the article and the one in this
    function is that the random restarts are not implemented here. This means that the
    sampled networks are not exactly statistically uniform. However, if the degrees 
    are small compared to the number of nodes the error is likely to be small.
    """
    assert sum(map(lambda x:x[0]*x[1],degs.items()))%2==0
    stubs=[]
    selfedges={}
    multiedges=set()
    edgetoindex={}
    nodes=sum(degs.values())

    node=0
    for k,num in degs.items():
        for i in range(num):
            for j in range(k):
                stubs.append(node)
            node+=1
    random.shuffle(stubs)

    for s in range(len(stubs)/2):
        node1,node2=sorted([stubs[2*s],stubs[2*s+1]])

        edgetoindex[(node1,node2)]=edgetoindex.get((node1,node2),[])+[2*s]

        if net[node1,node2]!=0:
            multiedges.add((node1,node2))

        if node1==node2:
            selfedges[node1]=selfedges.get(node1,[])+[2*s]
        else:
            net[node1,node2]=1

    for node,sis in selfedges.items():
        for si in sis:
            repeat=True
            while repeat:
                #select two edges at random
                e1i,e2i=map(lambda x:2*x,random.sample(xrange(len(stubs)/2),2))
                c=[node,stubs[e1i],stubs[e1i+1],stubs[e2i],stubs[e2i+1]]
                n2,n3=sorted([c[1],c[2]])
                n4,n5=sorted([c[3],c[4]])
                if len(set(c))==len(c):
                    if (n2,n3) not in multiedges and (n4,n5) not in multiedges:
                        if net[node,n2]==0 and net[node,n4]==0 and net[n3,n5]==0:                            
                            net[n2,n3]=0
                            net[n4,n5]=0
                            net[node,n2]=1
                            net[node,n4]=1
                            net[n3,n5]=1
                            stubs[si],stubs[si+1]=sorted([n3,n5])
                            stubs[e1i],stubs[e1i+1]=sorted([node,n2])
                            stubs[e2i],stubs[e2i+1]=sorted([node,n4])
                            repeat=False

    # Uncomment to check that everything ok so far:
    #import diagnostics
    #assert sum(map(lambda x:x[0]*x[1],diagnostics.degs(net).items()))/2.+sum(map(lambda x:len(edgetoindex[x[0],x[1]])-1,multiedges))==sum(map(lambda x:x[0]*x[1],degs.items()))/2.

    #for s in range(len(stubs)/2):
    #    n1,n2=stubs[2*s],stubs[2*s+1]
    #    assert net[n1,n2]==1,str(2*s)

    for n1,n2 in multiedges:
        for dummy in range(int(math.floor(len(edgetoindex[(n1,n2)])/2.))):
            repeat=True
            while repeat:
                #select two edges at random
                e1i,e2i=map(lambda x:2*x,random.sample(xrange(len(stubs)/2),2))
                c=[n1,n2,stubs[e1i],stubs[e1i+1],stubs[e2i],stubs[e2i+1]]
                n3,n4=sorted([c[2],c[3]])
                n5,n6=sorted([c[4],c[5]])
                if len(set(c))==len(c):
                    if (n3,n4) not in multiedges and (n5,n6) not in multiedges:
                        if net[n1,n3]==0 and net[n2,n4]==0 and net[n1,n5]==0 and net[n2,n6]==0:
                            if len(edgetoindex[n1,n2])==2:
                                net[n1,n2]=0
                            assert net[n3,n4]==1
                            assert net[n5,n6]==1
                            net[n3,n4]=0
                            net[n5,n6]=0
                            net[n1,n3]=1
                            net[n2,n4]=1
                            net[n1,n5]=1
                            net[n2,n6]=1
                            si1,si2=sorted([edgetoindex[n1,n2].pop(),edgetoindex[n1,n2].pop()])
                            stubs[si1],stubs[si1+1]=sorted([n1,n3])
                            stubs[si1],stubs[si1+1]=sorted([n2,n4])
                            stubs[e1i],stubs[e1i+1]=sorted([n1,n5])
                            stubs[e2i],stubs[e2i+1]=sorted([n2,n6])
                            repeat=False


def single_layer_er(net,nodes,p=None,edges=None):
    """Generates a realization of a monoplex Erdos-Renyi network.

    Parameters
    ----------
    net : MultilayerNetwork with aspects=0
       Empty network object that is to be filled.
    nodes : iterable
       Sequence of node labels.       
    p : float
       Probability that edges is present.
    edges : int
       Number of edges that are present.

    References
    ----------
    Efficient generation of large random networks. PRE 71, 036113 (2005) 
    """

    if (p==None and edges==None) or (p!=None and edges!=None):
        raise Exception("Give one of the parameters: p or edges.")

    n=len(nodes)
    for node in nodes:
        net.add_node(node)

    if p!=None:        
        if p==1.0:
            for node1 in nodes:
                for node2 in nodes:
                    if node1!=node2:
                        net[node1,node2]=1
        else:
            v,w=1,-1
            while (v < n):
                r=random.random()
                w=w+1+int(math.floor(math.log(1-r)/math.log(1-p)))
                while ((w >= v) and (v < n)):
                    w = w-v
                    v = v+1
                if (v < n):
                    net[nodes[v],nodes[w]]=1
    else:
        for edge_index in random.sample(xrange((n*(n-1))/2),edges):
            v=int(1+math.floor(-0.5+math.sqrt(0.25+2*edge_index)))
            w=edge_index-(v*(v-1))/2
            net[nodes[v],nodes[w]]=1

def conf(degs,aspects=0,couplings=("categorical",1.0)):
    """Independent configuration models for fully interconnected multiplex networks.

    Parameters
    ----------
    degs : dict or sequence of dicts
      If a monoplex network, then a single dict where keys are the
      degrees and values give the number of nodes. If more aspects,
      then degs is a sequence of same type of dictionaries.
    aspectes : int 
       Number of aspects in the network, 0 or 1.
    couplings : tuple
       The coupling types of the multiplex network object.

    Returns
    -------
    net : MultiplexNetwork
       The (multiplex) network produced with the configuration model.


    See also
    --------
    single_layer_conf : the function used to generate a network on each layer


    """
    if aspects==0:
        net=MultilayerNetwork(aspects=aspects)
        single_layer_conf(net,degs)
    elif aspects==1:
        nodes=None
        for ldegs in degs:
            assert nodes==None or sum(ldegs.values())==nodes, "Number of nodes in layers differ."
            nodes=sum(ldegs.values())
        net=MultiplexNetwork(couplings=aspects*[couplings])
        for l,ldegs in enumerate(degs):
            net.add_layer(l)
            single_layer_conf(net.A[l],ldegs)
    else:
        raise Exception("0 or 1 aspects, please.")

    return net


def er(n,p=None,edges=None):
    """Multiplex Erdos-Renyi model.

    Parameters
    ----------
    n : int, list of lists of nodes
       Number of nodes, or lists of nodes in each layer if network is not fully 
       interconnected.
    p : float or list of floats
       Connection probability, or list of connection probabilities for each layer.
    edges : int or list of int
       Number of edges, or list of number of edges in each layer.

    Returns
    -------
    net : MultiplexNetwork
       The (multiplex) network produced.

    See also
    --------
    single_layer_er : the function used to generate a network on each layer
    """
    # What kind of network?
    fic = not hasattr(n,'__iter__') #fully interconnected
    monoplex = (not hasattr(p,'__iter__')) and (not hasattr(edges,'__iter__')) and fic
 
    # Sanity check for parameters
    if (p==None and edges==None) or (p!=None and edges!=None):
        raise Exception("Give one of the parameters: p or edges.")
    if not fic:
        if hasattr(p,'__iter__'):
            assert len(n)==len(p)
        elif hasattr(edges,'__iter__'):
            assert len(n)==len(edges)

    
    # Create the network
    if monoplex:
        net=MultilayerNetwork(aspects=0)
    else:
        net=MultiplexNetwork(couplings=[('categorical',1.0)],fullyInterconnected=fic)
        if not hasattr(n,'__iter__'):
            if p!=None:
                nodes=map(lambda x:xrange(n),p)
                layers=xrange(len(p))
            else:
                nodes=map(lambda x:xrange(n),edges)
                layers=xrange(len(edges))
        else:
            nodes=n
            layers=xrange(len(n))
            if p!=None and (not hasattr(p,'__iter__')):
                p=map(lambda x:p,layers)
            if edges!=None and (not hasattr(edges,'__iter__')):
                edges=map(lambda x:edges,layers)
                

    # Fill in the edges
    if p!=None:
        if monoplex:
            single_layer_er(net,range(n),p=p)
        else:
            for l,lp,lnodes in zip(layers,p,nodes):
                net.add_layer(l)
                single_layer_er(net.A[l],lnodes,p=lp)
    else:
        if monoplex:
            single_layer_er(net,range(n),edges=edges)
        else:
            for l,ledges,lnodes in zip(layers,edges,nodes):
                net.add_layer(l)
                single_layer_er(net.A[l],lnodes,edges=ledges)

    return net

def er_partially_interconnected(nodes,ps,couplings=('categorical',1.0)):
    """Generate multiplex Erdos-Renyi network which is not fully interconnected.

    The produced multiplex network has a single aspect.

    Parameters
    ----------
    nodes : list of lists 
       List of lists of nodes, where each list corresponds to
       nodes in one layer.
    ps : list
       List of edge occupation probabilities for layers
    couplings : tuple
       The coupling types of the multiplex network object.

    Returns
    -------
    net : MultiplexNetwork
       The multiplex network that is produced.    
    """
    assert len(nodes)==len(ps)
    net=MultiplexNetwork(couplings=[couplings],fullyInterconnected=False)
    for layer,lnodes in enumerate(nodes):
        net.add_layer(layer)
        single_layer_er(net.A[layer],lnodes,ps[layer])
    return net

def full(nodes,layers,couplings=('categorical',1.0)):
    """Generate a full multiplex network.

    The produced multiplex network has a single aspect and is fully
    interconnected. Can also produce a full monoplex network.

    Parameters
    ----------
    nodes : int
       Number of nodes in the network
    layers : int, sequence or None
       Number of layers in the network, a sequence of layer names, or
       None for monoplex networks.
    couplings : tuple
       The coupling types of the multiplex network object.

    Returns
    -------
    net : MultiplexNetwork or MultilayerNetwork
       The multiplex network that is produced, or the monoplex
       network (which is of type MultilayerNetwork).
    """
    if layers==None:
        n=MultilayerNetwork(aspects=0)
        for node1 in range(nodes):
            for node2 in range(nodes):
                if node1!=node2:
                    n[node1,node2,layer,layer]=1
    elif not hasattr(layers,'__iter__'): #is not sequence
        n=MultiplexNetwork(couplings=[couplings])
        for layer in range(layers):
            for node1 in range(nodes):
                for node2 in range(nodes):
                    if node1!=node2:
                        n[node1,node2,layer,layer]=1
    else: #it's a sequence
        n=MultiplexNetwork(couplings=[couplings])
        for layer in layers:
            for node1 in range(nodes):
                for node2 in range(nodes):
                    if node1!=node2:
                        n[node1,node2,layer,layer]=1

    return n

def full_multilayer(nodes,layers):
    """Generate a full multilayer network.

    The generated network has a single aspect, and all the inter-layer 
    and intra-layer edges.

    Parameters
    ----------
    nodes : int
       Number of nodes in the network
    layers : int or sequence
       Number of layers in the network, or a sequence of layer names

    Returns
    -------
    net : MultilayerNetwork
       The multilayer network that is produced.
    """
    if not hasattr(layers,'__iter__'): #is not sequence
        layers=range(layers)

    n=MultilayerNetwork(aspects=1)
    for layer1 in layers:
        for layer2 in layers:
            for node1 in range(nodes):
                for node2 in range(nodes):
                    if node1!=node2 or layer1!=layer2:
                        n[node1,node2,layer1,layer2]=1
    return n

def er_multilayer(nodes,layers,p,randomWeights=False):
    """Generate multilayer Erdos-Renyi network.

    The produced multilayer network has a single aspect.

    Parameters
    ----------
    nodes : int
       Number of nodes in the network
    layers : int or sequence
       Number of layers in the network, or a sequence of layer names
    p : float
       The edge probability
    randomWeights : bool
       If true the weights are uniformly random between (0,1].

    Returns
    -------
    net : MultilayerNetwork
       The multilayer network that is produced.
    """


    if not hasattr(layers,'__iter__'): #is not sequence
        layers=range(layers)

    n=MultilayerNetwork(aspects=1)
    for layer1 in layers:
        for layer2 in layers:
            for node1 in range(nodes):
                for node2 in range(node1+1,nodes):
                    if node1!=node2 or layer1!=layer2:
                        if random.random()<p:
                            if randomWeights:
                                n[node1,node2,layer1,layer2]=random.random()
                            else:
                                n[node1,node2,layer1,layer2]=1

    return n