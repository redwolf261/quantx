import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple

class EconomicRegime(Enum):
    BULL_MARKET = "bull"
    BEAR_MARKET = "bear"
    RECESSION = "recession"
    HIGH_INFLATION = "high_inflation"
    NORMAL = "normal"

@dataclass
class RegimeCharacteristics:
    equity_mean: float
    equity_vol: float
    debt_mean: float
    debt_vol: float
    inflation_rate: float
    job_loss_prob: float

class EconomicCycleEngine:
    """
    Models economic cycles using a Markov Chain transition matrix.
    Provides characteristics for the current regime.
    """
    def __init__(self):
        # Baseline characteristics
        self.characteristics = {
            EconomicRegime.NORMAL: RegimeCharacteristics(
                equity_mean=0.12, equity_vol=0.15, debt_mean=0.07, debt_vol=0.03, inflation_rate=0.05, job_loss_prob=0.02
            ),
            EconomicRegime.BULL_MARKET: RegimeCharacteristics(
                equity_mean=0.20, equity_vol=0.18, debt_mean=0.06, debt_vol=0.03, inflation_rate=0.06, job_loss_prob=0.01
            ),
            EconomicRegime.BEAR_MARKET: RegimeCharacteristics(
                equity_mean=-0.15, equity_vol=0.28, debt_mean=0.08, debt_vol=0.04, inflation_rate=0.04, job_loss_prob=0.05
            ),
            EconomicRegime.RECESSION: RegimeCharacteristics(
                equity_mean=-0.05, equity_vol=0.22, debt_mean=0.05, debt_vol=0.05, inflation_rate=0.02, job_loss_prob=0.10
            ),
            EconomicRegime.HIGH_INFLATION: RegimeCharacteristics(
                equity_mean=0.08, equity_vol=0.20, debt_mean=0.04, debt_vol=0.06, inflation_rate=0.09, job_loss_prob=0.03
            ),
        }
        
        # Annual Transition Matrix
        self.states = [r for r in EconomicRegime]
        
        # Probability of moving from row to column
        self.transition_matrix = np.array([
            # Bull, Bear, Recession, High_Inf, Normal
            [0.60, 0.20, 0.05, 0.05, 0.10], # Bull
            [0.20, 0.10, 0.30, 0.00, 0.40], # Bear
            [0.20, 0.10, 0.20, 0.00, 0.50], # Recession
            [0.10, 0.20, 0.30, 0.30, 0.10], # High_Inf
            [0.25, 0.10, 0.05, 0.10, 0.50], # Normal
        ])
        
    def generate_regime_path(self, years: int, start_regime: EconomicRegime = EconomicRegime.NORMAL, num_simulations: int = 1) -> np.ndarray:
        """
        Generates a 2D numpy array of shape (years, num_simulations) containing the integer index of the regime for each year.
        Uses vectorized numpy choice.
        """
        path = np.zeros((years, num_simulations), dtype=int)
        
        start_idx = self.states.index(start_regime)
        current_states = np.full(num_simulations, start_idx)
        path[0, :] = current_states
        
        # Precompute cumsums for fast sampling
        cum_trans = np.cumsum(self.transition_matrix, axis=1)
        
        for t in range(1, years):
            rand_vals = np.random.rand(num_simulations, 1)
            # Find the next state based on current state probabilities
            # current_states holds the row index for each simulation
            probs = cum_trans[current_states] # Shape: (num_simulations, len(states))
            next_states = (rand_vals > probs).sum(axis=1)
            path[t, :] = next_states
            current_states = next_states
            
        return path
        
    def get_characteristics(self, regime: EconomicRegime) -> RegimeCharacteristics:
        return self.characteristics[regime]
