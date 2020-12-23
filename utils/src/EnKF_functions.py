# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 10:30:42 2020

@author: jzwart
functions for updating LSTM states using ensemble Kalman filter 
"""
import numpy as np 

def combine_lstm_states(preds, h, c):
    '''
    Combining lstm states for updating in EnKF. Should always be in the order of preds, h, c. 
    
    '''
    out = np.concatenate((preds, h, c), )
    return out


def get_Y_vector(n_states_est, n_step, n_en):
    '''
    Vector for holding states (and parameters) for updating with EnKF 

    :param int n_states_est: number of states we're updating in data assimilation routine
    :param int n_step: number of model timesteps
    :param int n_en: number of ensembles
    '''
    Y = np.empty((n_states_est, n_step, n_en))
    Y[:] = np.NaN
    return Y 

def get_obs_error_matrix(n_states_obs, n_step, state_sd):
    '''
    Observation error matrix, should be a square matrix where col & row = the number of states (and params) for which you have observations; most likely we only have observations for temperature so n_states_obs will probably be the number of stream segments we're modeling 
    
    :param int n_states_obs: number of states we have observations for 
    :param int n_step: number of model timesteps
    :parma state_sd: vector of state observation standard deviation; assuming sd is constant through time
    '''
    R = np.zeros((n_states_obs, n_states_obs, n_step))
    
    state_var = state_sd**2 # variance of temperature observations 
    
    for i in range(n_step):
        # variance is the same for each depth and time step; could make dynamic or varying by time step if we have good reason to do so
        np.fill_diagonal(R[:,:,i], state_var)
    
    return R 

def get_obs_id_matrix(n_states_obs, n_states_est, n_step, obs_mat):
    '''
    Measurement operator matrix saying 1 if there is observation data available, 0 otherwise
    
    :param int n_states_obs: number of states we have observations for 
    :param int n_states_est: number of states we're estimating - should include predicted states (e.g. water temp) and LSTM states (e.g. h & c) 
    :param int n_step: number of model timesteps 
    :param matrix obs_mat: observation matrix created with get_obs_matrix function     
    '''
    H = np.zeros((n_states_obs, n_states_est, n_step))
    
    for t in range(n_step):
        H[0:n_states_obs, 0:n_states_obs, t] = np.where(np.isnan(obs_mat[:,:,t]), 0, 1) # this needs to be a diagonal if predicting for more than 1 stream segment 
        
    return H


def get_obs_matrix(obs_array, model_locations, n_step, n_states_obs):
    '''
    turn observation array into matrix
    
    :param obs_array: observation array 
    :param model_location: stream segments where we're predicting states 
    :param n_step: number of model timesteps 
    :param n_states_obs: number of states we have observations for     
    '''
    obs_mat = np.empty((n_states_obs, 1, n_step))
    obs_mat[:] = np.NaN 
    
    for i in range(len(model_locations)):
        cur_site = obs_array[i,:,:]
        obs_mat[i,0,:] = np.reshape(cur_site, (1, n_step))
    
    return obs_mat

#  NEED TO MAKE THIS INTO PYTHON CODE ## 
def kalman_filter(Y,
                  R,
                  obs,
                  H,
                  n_en,
                  cur_step,
                  n_states_est): 
    '''
    
    '''

    cur_obs = obs[ , , cur_step]

    cur_obs = ifelse(is.na(cur_obs), 0, cur_obs) # setting NA's to zero so there is no 'error' when compared to estimated states

    ###### estimate the spread of your ensembles #####
    Y_mean = matrix(apply(Y[ , cur_step, ], MARGIN = 1, FUN = mean), nrow = length(Y[ , 1, 1])) # calculating the mean of each temp and parameter estimate
    delta_Y = Y[ , cur_step, ] - matrix(rep(Y_mean, n_en), nrow = length(Y[ , 1, 1])) # difference in ensemble state/parameter and mean of all ensemble states/parameters

    # estimate Kalman gain w/o covar_inf_factor #
    K = ((1 / (n_en - 1)) * delta_Y %*% t(delta_Y) %*% t(H[, , cur_step])) %*%
      qr.solve(((1 / (n_en - 1)) * H[, , cur_step] %*% delta_Y %*% t(delta_Y) %*% t(H[, , cur_step]) + R[, , cur_step]))

    # update Y vector #
    for(q in 1:n_en): 
      Y[, cur_step, q] = Y[, cur_step, q] + K %*% (cur_obs - H[, , cur_step] %*% Y[, cur_step, q]) # adjusting each ensemble using kalman gain and observations

  return Y 


