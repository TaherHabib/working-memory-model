import numpy as np
import pandas as pd


class HTM_CELL():
    
    """
    
    """
    
    def __init__(self, i=None, j=None, M=None, N=None, n_dendrites=None, n_synapses=None, 
                 nmda_th=None, perm_th=None, perm_init=None, perm_init_sd=None):
        
        """
        
        """
        
        self.M = M # number of cells per minicolumn
        self.N = N # number of minicolumns
        
        self.n_dendrites = n_dendrites # number of dendritic segments on a single cell
        self.n_synapses = n_synapses # total number of CONNECTED synapses on a single dendritic segment
        
        self.nmda_th = nmda_th
        self.perm_th = perm_th
        self.perm_init = perm_init
        self.perm_init_sd = perm_init_sd
        
        # list containing the matrices of potential synapses (permanence values) for each dendrite
        # of the HTM cell; numpy array of 32 MxN matrices, shape: (32,M,N)
        self.dendrites = np.array([np.random.normal(loc=self.perm_init, scale=self.perm_init_sd, size=[self.M, self.N])
                          for i in range(self.n_dendrites)], dtype=np.float64)
        
        # Preventing all autapses
        for d in range(self.n_dendrites):
            self.dendrites[d,i,j] = 0.0
        
        self.dutycycle = []
        
        
        return
    
    
    def get_cell_connSynapses(self):
        """
        For getting the connected synapses on all the dendrites of the cell.
        
        Returns
        -------
        A Boolean array of size (n_dendrites, M, N)

        """
        
        connected_synapses = np.array(self.dendrites > self.perm_th) # boolean list of 32 MxN binary matrices, 
                                                                     # shape: (32,M,N)
        return connected_synapses
            
        
    def get_cell_synaPermanences(self):
        """
        For getting the permanence values of all synapses on all the dendrites 
        of the cell.
        
        Returns
        -------
        A Boolean array of size (n_dendrites, M, N)

        """
        
        return self.dendrites
    
    
    def update_cell_dutycycle(self, prev_state=None, prev_pred=None):
        
        
        return None