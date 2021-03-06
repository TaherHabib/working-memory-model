"""
FILE DESCRIPTION:
------------------------

    
"""

import numpy as np
import pandas as pd
import random

from ufuncs import dot_prod, get_idx_nonZeroElements

class HTM_CELL():
    
    def __init__(self, cellsPerColumn=None, numColumns=None, columnsPerChar=None,
                 maxDendritesPerCell=None, maxSynapsesPerDendrite=None, 
                 nmdaThreshold=None, permThreshold=None, permInit=None, permInit_sd=None,
                 perm_decrement=None, perm_increment=None, perm_decay=None,
                 dendriteDuty_UpperLimit=None):
        
        self.M = cellsPerColumn
        self.N = numColumns
        self.k = columnsPerChar

        self.maxDendritesPerCell = maxDendritesPerCell
        self.maxSynapsesPerDendrite = maxSynapsesPerDendrite # max. number of CONNECTED synapses on a 
                                                             # single dendritic segment.
        self.nmdaThreshold = nmdaThreshold
        self.permThreshold = permThreshold
        self.permInit = permInit
        self.permInit_sd = permInit_sd
        
        self.perm_decrement = perm_decrement
        self.perm_increment = perm_increment
        self.perm_decay = perm_decay
        
        # list containing the (numpy array) MxN matrices of potential synapses (permanence values) for each dendrite
        # of the HTM cell; shape: (<maxDendritesPerCell>,M,N). There are NO dendrites initially.
        self.dendrites = [None for i in range(maxDendritesPerCell)]
        self.dendrites_dutyCycle = [None for i in range(maxDendritesPerCell)]
        
        self.highDecayFactor = 30
        self.dendriteDuty_UpperLimit = dendriteDuty_UpperLimit #int(avgLen_reberString*self.M*self.maxDendritesPerCell*4)
        
        return
    
    
    def get_cell_numDendrites(self):
        
        numDendrites = 0
        for dendrite in self.dendrites:
            if dendrite is None:
                continue
            else:
                numDendrites+=1
        
        return numDendrites
    
    
    def get_cell_numUnusedDendrites(self):
        
        num_UnusedDendrites = 0
        for dendrite in self.dendrites:
            if dendrite is None:
                num_UnusedDendrites += 1
            else:
                continue
        
        return num_UnusedDendrites
    
    
    def get_cell_numSynapsesOnDendrite(self, dendrite_idx=None):
        
        return np.count_nonzero(self.dendrites[dendrite_idx])

    
    def grow_cell_newDendrite(self, prev_winnerCells=None):
        
        
        newDendrite = np.array(np.random.normal(loc=self.permInit, scale=self.permInit_sd, size=[self.M, self.N]),
                               dtype=np.float64)
        
        # A Dendrite will only have maximum <maxSynapsesPerDendrite> synapses.
        # Hence, if there are more than <k> winner cells in 'prev_winnerCells',
        # then <k> are randomly chosen for synaptic connection.
        if np.count_nonzero(prev_winnerCells) > self.k:
            prev_winnerCells_ = np.zeros(shape=[self.M, self.N])
            
            random.seed()
            list_prev_WinnerCells_idx = random.choices(get_idx_nonZeroElements(prev_winnerCells), k=self.k)
            
            for i in list_prev_WinnerCells_idx:
                prev_winnerCells_[i] = 1
        
        else:
            prev_winnerCells_ = prev_winnerCells
        
        newDendrite = newDendrite*prev_winnerCells_
        # 'newDendrite' will ONLY have connections (at permInit level) to 
        # 'presynaptic_WinnerCells'. The rest will be all 0.0. Any dendrite 
        # will have atmost <maxSynapsesPerDendrite> synapses.
        
        newDendrite_idx = None
        
        # 'newDendrite' will be assigned to the first "non-NONE" index in 
        # self.dendrites array
        for i in range(self.maxDendritesPerCell):
            if self.dendrites[i] is None:
                newDendrite_idx = i
                self.dendrites[newDendrite_idx] = newDendrite
                self.dendrites_dutyCycle[newDendrite_idx] = self.dendriteDuty_UpperLimit
                break
            else:
                continue
        
        return newDendrite_idx
    
    
    def grow_cell_newSynapsesOnDendrite(self, dendrite_idx=None, prev_winnerCells=None):
        
        list_prev_WinnerCells_idx = get_idx_nonZeroElements(prev_winnerCells)
        
        newSynapsesCapacity = self.maxSynapsesPerDendrite - self.get_cell_numSynapsesOnDendrite(dendrite_idx)
        numNewSynapses = 0
        
        while len(list_prev_WinnerCells_idx)>0 and newSynapsesCapacity>0:
            preSynapticWinnerCell = random.choice(list_prev_WinnerCells_idx)
            
            # If there is no synapse existing between 'preSynapticWinnerCell' and the 'dendrite_idx',
            # create one synapse!
            if self.dendrites[dendrite_idx][preSynapticWinnerCell] == 0.0:
                self.dendrites[dendrite_idx][preSynapticWinnerCell] = np.random.normal(loc=self.permInit, 
                                                                                       scale=self.permInit_sd)
                self.dendrites_dutyCycle[dendrite_idx] = self.dendriteDuty_UpperLimit
                newSynapsesCapacity -= 1
                numNewSynapses += 1
                
            list_prev_WinnerCells_idx.remove(preSynapticWinnerCell)
            
        return numNewSynapses, list_prev_WinnerCells_idx
    
    
    def update_cell_dendritePermanences(self, dendrite_idx=None, prev_state=None, decay=False, high_decay=False):
        
        prev_state_ = (self.dendrites[dendrite_idx]*prev_state)>0
        prev_state_ = prev_state_.astype(int)
            
        if decay:
            self.dendrites[dendrite_idx] = self.dendrites[dendrite_idx] - self.perm_decay*prev_state_
        
        elif high_decay:
            self.dendrites[dendrite_idx] = self.dendrites[dendrite_idx] - self.highDecayFactor*self.perm_decay*prev_state_
        
        
        else:
            self.dendrites[dendrite_idx] = self.dendrites[dendrite_idx] + self.perm_increment*prev_state_ - self.perm_decrement
            
        # Pruning Negative Permanence values (setting to 0.0)
        self.dendrites[dendrite_idx][self.dendrites[dendrite_idx] < 0] = 0.0
        
        # Pruning Positive Permanence values (setting to 1.0)
        self.dendrites[dendrite_idx][self.dendrites[dendrite_idx] > 1] = 1.0
        
        return prev_state_, self.get_cell_numSynapsesOnDendrite(dendrite_idx)
    
    
    def undo_cell_dendriteReinforcement(self, dendrite_idx=None, reinforcedSynapses=None):
        
        
        nonzeroSynapses = np.zeros(shape=[self.M, self.N])
        list_reinforcedSynapses_idx = get_idx_nonZeroElements(reinforcedSynapses)
        list_nonzeroSynapses_idx = get_idx_nonZeroElements(self.dendrites[dendrite_idx]>0)
        list_nonzeroSynapses_idx = set(list_nonzeroSynapses_idx) - set(list_nonzeroSynapses_idx).intersection(list_reinforcedSynapses_idx)
        
        for i in list_nonzeroSynapses_idx:
                nonzeroSynapses[i] = 1        
        
        self.dendrites[dendrite_idx] = self.dendrites[dendrite_idx] - self.perm_increment*reinforcedSynapses + self.perm_decrement*nonzeroSynapses
        
        return
    
    
    def reset_cell_dendrite(self, dendrite_idx=None, resetSynapses=None):
        
        mask_otherSynapses = (1 - resetSynapses)*self.dendrites[dendrite_idx]
    
        self.dendrites[dendrite_idx] = mask_otherSynapses + np.array(np.random.normal(loc=self.permInit, scale=self.permInit_sd, size=[self.M, self.N]), 
                                                                     dtype=np.float64)*resetSynapses
        
        self.dendrites_dutyCycle[dendrite_idx] = self.dendriteDuty_UpperLimit
        
        return
    
    
    def get_cell_connectedSynapses(self):
        """
        For getting the connected synapses on all the dendrites of the cell.
        
        """
        
        cell_connectedSynapses = []
        
        for dendrite in self.dendrites:
            if dendrite is None:
                cell_connectedSynapses.append(None)
            else:
                cell_connectedSynapses.append(dendrite>self.permThreshold)
        
        return cell_connectedSynapses # numpy array of length <maxDendritesPerCell> of either 
                                        # 'None' elements or MxN (numpy) boolean matrices.        
                    
    def get_cell_predictivity(self, net_state=None):
        """
        Checks if the cell is in a predictive state, given the current 
        timestep's network activity.

        Parameters
        ----------
        net_state : binary array of shape (MxN). 
        Containing the activity of cell population from current time step.
    
        Returns
        -------
        None.

        """

        # 'dendritesSpikes' will be a list containing <maxDendritesPerCell> elements,
        # either 'None' if the dendrites have NO synapses; OR, a boolean value.
        dendritesSpikes = [] 
        
        cell_predictivity = False
        predDendrites = None # stores the indices of all dendrites that led to the prediction
                             # of the cell.
                             
        cell_connectedSynapses = self.get_cell_connectedSynapses() 
                
        for dendrite in cell_connectedSynapses:
            if dendrite is None:
                dendritesSpikes.append(None)
            else:
                # 'is_nmdaSpike' is a numpy boolean array of length 1, with either a True or False.
                is_nmdaSpike = dot_prod(net_state, dendrite)>self.nmdaThreshold
                dendritesSpikes.append(is_nmdaSpike[0])
            
        if any(dendritesSpikes):
            cell_predictivity = True
            predDendrites = np.where(dendritesSpikes)[0] # 1D numpy array of max. possible length 
                                                         # <maxDendritesPerCell>, with integer entries
                                                         # between 0 and <maxDendritesPerCell>-1.                          
            for dendrite_idx in predDendrites:
                self.dendrites_dutyCycle[dendrite_idx] = self.dendriteDuty_UpperLimit
            
        return cell_predictivity, predDendrites
    
    
    def get_cell_allDendrites(self):
        """
        For getting the permanence values of all synapses on all the dendrites 
        of the cell.
        
        """
        
        return np.array(self.dendrites, dtype=object)    
    