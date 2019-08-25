
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
        self.current_price = 0
        self.prev_usdt,self.prev_btc = 0,0
        #self.init_btc = self.btc_holdings
        self.max_btc = 0
        self.max_usdt = 0
        self.btc_returns = 0
        self.return_df = pd.DataFrame()
        self.current_act = 0
        self.trades = pd.DataFrame()
        self.balances = pd.DataFrame()
        self.dates = df["Close time"]
        self.last_entry = 0
        self.last_exit = 0
        self.last_entry_t = 0
        self.last_exit_t = 0
        self.reward = 0
        

        self.df = df
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Box(
            low=np.array([0, 0]), high=np.array([3, 1]), dtype=np.float16)

        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(6, 6), dtype=np.float16)
        

    def _next_observation(self):
        # Get the hist data at step
        frame = np.array([
            self.df["Open"].iloc[self.current_step],
            self.df["High"].iloc[self.current_step],
            self.df["Low"].iloc[self.current_step],
            self.df["Close"].iloc[self.current_step],
            self.df["Volume"].iloc[self.current_step],
            #self.df["Position"].iloc[self.current_step],
        ])
        return frame

    def _take_action(self, action):
        #nested buy sell functions
        def buy():
            total_possible = float(self.usdt_holdings / self.current_price)
            #update trade df
            trade_stamp = portmaker.to_dt(self.df["Close time"].iloc[self.current_step])
            trade = pd.DataFrame({"Date":trade_stamp,"USDT":int(self.usdt_holdings),"BTC":self.btc_holdings,"Type":"BUY","Price":self.current_price},index=[0])
            self.trades = pd.concat([self.trades,trade])
            
            #set last entry to current price
            self.last_entry = self.current_price
            # Buy amount % of balance in shares
            
            
            #update balances
            
            
            total_possible = round(total_possible,5)
            #update balances
            #deduct spent usdt from usdt_holdings 
            self.usdt_holdings = self.usdt_holdings -(total_possible*self.current_price)
            self.btc_holdings = total_possible
            bal = pd.DataFrame({"Date":trade_stamp,"USDT":int(self.usdt_holdings),"BTC":self.btc_holdings,"Price":self.current_price},index=[0])
            self.balances = pd.concat([self.balances,bal])
            #update max btc held
            if total_possible > self.max_btc:
                self.max_btc = self.btc_holdings
            print("Buy {}btc at {}\t{}".format(total_possible,str(self.current_price),trade_stamp))
            
        def sell():
            trade_stamp = portmaker.to_dt(self.df["Close time"].iloc[self.current_step])
            self.last_exit = self.current_price
            total_possible = float(self.btc_holdings)#/float(last_price["bidPrice"])
            print("Sell {} btc at {}\t{}".format(total_possible,df["Close"].iloc[self.current_step],trade_stamp))
            #update balances
            self.btc_holdings = self.btc_holdings -self.btc_holdings
            self.usdt_holdings = float(total_possible*self.current_price)
            #update trade df
            #trade_stamp = portmaker.to_dt(self.df["Close time"].iloc[self.current_step])
            trade = pd.DataFrame({"Date":trade_stamp,"USDT":int(self.usdt_holdings),"BTC":total_possible,"Type":"SELL","Price":self.current_price},index=[0])
            bal = pd.DataFrame({"Date":trade_stamp,"USDT":int(self.usdt_holdings),"BTC":self.btc_holdings,"Price":self.current_price},index=[0])
            self.balances = pd.concat([self.balances,bal])    
            self.trades = pd.concat([self.trades,trade])    
            
        # Set the current price to a random price within the current time step
        self.current_price = random.uniform(self.df["Open"].iloc[self.current_step], self.df["Close"].iloc[self.current_step])
        #print(current_price,self.df["Open"].iloc[self.current_step])
        action_type = action[0]
        self.current_act = action_type
        #external purchase quantity
        amount = action[1]
        """
        BUY BTC
        ==============
        Conditions are:
        -if action is buy
        -has usdt to buy btc
        -current signal is not a same as previous signal
        -has no btc
        ==============
        """
        
            
            
        if (action_type > 0 and self.usdt_holdings !=0 and self.last_sig!=action_type and self.btc_holdings ==0):
            #overtrading limiter 2
            td = self.current_price/self.last_exit
            if(td > .99 and td < 1.01):
                pass
                #print("no trades", self.df.index.values[self.current_step],self.current_step)
            else:
                buy()
            

        elif (action_type < 0 and self.btc_holdings !=0 and self.last_sig!=action_type):
            # Buy amount % of balance in shares
            td = self.current_price/self.last_entry
            #prevent action at less the +-1% delta
            #backtest a multitude of these tolerances to tune R/R
            if(td > .99 and td < 1.01):
                pass
                #uncomment to see possible overtrade
                #print("no trades", self.df.index.values[self.current_step],self.current_step)
                #df["Position"].iloc[self.current_step]
            else:
                sell()
                
                
                
        
            if self.usdt_holdings > self.max_usdt:
                self.max_usdt = self.usdt_holdings
            #print("Selling {}btc at {}".format(total_possible,str(current_price)))
            #print("{} remaining usdt".format(self.usdt_holdings))
            #print("\n====\n")
            
            
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
            
                #print("USDT: {}  Init btc: {}".format(self.usdt_holdings,self.init_btc))
            self.prev_usdt,self.prev_btc = self.usdt_holdings,self.btc_holdings
            #print("Current profit: ",curr_profit)"""


    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)

        self.current_step += 1

        if self.current_step > len(self.df['Open'].values) - 6:
            self.current_step = 0

        delay_modifier = (self.current_step / MAX_STEPS)
        if(self.btc_holdings!=0):
            self.reward = self.btc_holdings/self.init_btc
        elif(self.btc_holdings==0 and self.usdt_holdings!=0):
            curr_btc = float(self.usdt_holdings / self.current_price)
            self.reward = curr_btc/self.init_btc
            
        done = (self.btc_holdings/self.init_btc == 0 and self.usdt_holdings==0)
        if(self.current_step == len(df)-1):
            done = True

        obs = self._next_observation()

        return obs, self.reward, done, {}

    def reset(self):
        # Reset the state of the environment to an initial state
        self.usdt_holdings = 1000
        self.btc_holdings = 0
        self.max_usdt = self.usdt_holdings
        self.max_btc = 0
        self.max_usdt = 0
        self.btc_returns = 0
        self.return_df = pd.DataFrame()
        self.current_act = 0
        self.current_price = 0
        self.init_btc = (self.usdt_holdings/df['Open'].iloc[self.current_step])
        self.init_usdt = self.usdt_holdings
        self.trades = pd.DataFrame()
        self.balances = pd.DataFrame()
        self.last_entry = 0
        self.last_exit = 0
        self.last_entry_t = 0
        self.last_exit_t = 0
        self.reward = 0

        # Set the current step to a random point within the data frame
        #print(self.df.columns)
        self.current_step = 0#random.randint(0, len(self.df['Open'].values) - 6)

        return self._next_observation()

    def render(self, mode='human', close=False):
        curr_profit = self.reward
        # Render the environment to the screen
        #profit = (self.btc_holdings/ self.init_btc)
        if(self.reward>0):
            curr_profit*=100
        else:
            profit = (1-curr_profit)*100
        max_curr = (self.max_btc/self.init_btc)*100
        
        
        print(f'Step: {self.current_step}')
        print("Timestamp: ",portmaker.to_dt(self.df["Close time"].iloc[self.current_step]))
        print("-------------")
        print(f'Current BTC Balance: {self.btc_holdings}')
        print("Init BTC: ",self.init_btc)
        print("-------------")
        print("Current USDT Balance: {}".format(self.usdt_holdings))
        print("Init USDT: ",self.init_usdt)
        print("-------------")
        print("-------------")
        print('Max usdt: {}'.format(self.max_usdt))
        print(f'Max btc: {self.max_btc}')
        print('Max profit at step: {}'.format(max_curr))
        #print(f'Profit: {profit}')
        if(self.current_step == len(df)-8):
            make_plots()
        #print(df.iloc[self.current_step].index)