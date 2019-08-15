import random
import json
import gym
from gym import spaces
import pandas as pd
import numpy as np

MAX_STEPS = 20000
class TradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, df):
        super(TradingEnv, self).__init__()
        self.last_sig = 0
        self.usdt_holdings = 1000
        self.btc_holdings = 0
        self.current_step = 0
        self.prev_usdt,self.prev_btc = 0,0
        #self.init_btc = self.btc_holdings
        self.max_btc = 0
        self.max_usdt = 0
        self.btc_returns = 0
        self.current_act = 0
        

        self.df = df
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Box(
            low=np.array([0, 0]), high=np.array([3, 1]), dtype=np.float16)

        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(6, 6), dtype=np.float16)
        

    def _next_observation(self):
        # Get the stock data points for the last 5 days and scale to between 0-1
        frame = np.array([
            self.df["Open"].iloc[self.current_step],
            self.df["High"].iloc[self.current_step],
            self.df["Low"].iloc[self.current_step],
            self.df["Close"].iloc[self.current_step],
            self.df["Volume"].iloc[self.current_step],
        ])

        # Append additional data and scale each value to between 0-1
        #print(self.total_sales_value / (MAX_NUM_SHARES * MAX_SHARE_PRICE))
        """obs = np.append(frame, [[
            self.balance / 1,
            self.max_net_worth / MAX_ACCOUNT_BALANCE,
            self.shares_held / MAX_NUM_SHARES,
            self.cost_basis / MAX_SHARE_PRICE,
            self.total_shares_sold / MAX_NUM_SHARES,
            self.total_sales_value / (MAX_NUM_SHARES * MAX_SHARE_PRICE),
        ]], axis=0)"""
        return frame

    def _take_action(self, action):
        # Set the current price to a random price within the time step
        current_price = random.uniform(self.df["Open"].iloc[self.current_step], self.df["Close"].iloc[self.current_step])
        #print(current_price,self.df["Open"].iloc[self.current_step])
        action_type = action[0]
        self.current_act = action_type
        amount = action[1]
        #BUY condition
        if (action_type > 0 and self.usdt_holdings !=0 and self.last_sig!=action_type ):
            
            # Buy amount % of balance in shares
            total_possible = float(self.usdt_holdings / current_price)
            self.usdt_holdings = self.usdt_holdings -(total_possible*current_price)
            total_possible = round(total_possible,5)
            #update balances
            self.btc_holdings = total_possible
            if total_possible > self.max_btc:
                self.max_btc = self.btc_holdings
            print("buying {}btc at {}".format(total_possible,str(current_price)))
            print("{} remaining usdt".format(self.usdt_holdings))
            print("\n====\n")
            

        elif (action_type < 0 and self.btc_holdings !=0 and self.last_sig!=action_type):
            # Buy amount % of balance in shares
            total_possible = float(self.btc_holdings)#/float(last_price["bidPrice"])
            
            #update balances
            self.btc_holdings = self.btc_holdings -self.btc_holdings
            self.usdt_holdings = float(total_possible*current_price)
            if self.usdt_holdings > self.max_usdt:
                self.max_usdt = self.usdt_holdings
            print("Selling {}btc at {}".format(total_possible,str(current_price)))
            print("{} remaining usdt".format(self.usdt_holdings))
            print("\n====\n")
            
            
        self.last_sig  = action[0]
        if(self.btc_holdings!=0):
            self.btc_net = (self.btc_holdings/self.init_btc)*100

        if self.btc_holdings > self.max_btc:
            self.max_btc = self.btc_holdings
        if self.btc_holdings>0:
            curr_profit = (self.btc_holdings/ self.init_btc)
            #print(self.btc_holdings,self.init_btc)
        else:
            #print("USDT: {}  Init btc: {}".format(self.usdt_holdings,self.init_btc))
            if(self.usdt_holdings != self.prev_usdt):
                print("USDT: {}  Init btc: {}".format(self.usdt_holdings,self.init_btc))
            self.prev_usdt,self.prev_btc = self.usdt_holdings,self.btc_holdings
            #print("Current profit: ",curr_profit)


    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)

        self.current_step += 1

        if self.current_step > len(self.df['Open'].values) - 6:
            self.current_step = 0

        delay_modifier = (self.current_step / MAX_STEPS)

        #reward = self.btc_net
        done = (self.btc_holdings/self.init_btc == 0 and self.usdt_holdings==0)

        obs = self._next_observation()

        return obs,  done, {}

    def reset(self):
        # Reset the state of the environment to an initial state
        self.usdt_holdings = 1000
        self.btc_holdings = 0
        self.max_usdt = self.usdt_holdings
        self.max_btc = 0
        self.max_usdt = 0
        self.btc_returns = 0
        self.current_act = 0
        self.init_btc = (self.usdt_holdings/df['Open'].iloc[self.current_step])

        # Set the current step to a random point within the data frame
        #print(self.df.columns)
        self.current_step = random.randint(
            0, len(self.df['Open'].values) - 6)

        return self._next_observation()

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        profit = (self.btc_holdings/ self.init_btc)
        if(profit>0):
            profit*=100
        else:
            profit = (1-profit)
        max_curr = (self.max_btc*self.df['Open'].iloc[-1])
        
        
        print(f'Step: {self.current_step}')
        print(f'BTC Balance: {self.btc_holdings}')
        print("USDT Balance: {}".format(self.usdt_holdings))
        print('Max usdt: {}'.format(self.max_usdt))
        print(f'Max btc: {self.max_btc}')
        print('Max btc at current price: {}'.format(max_curr))
        print(f'Profit: {profit}')
        #print(df.iloc[self.current_step].index)
        return {"USDT":self.usdt_holdings,"BTC":self.btc_holdings}