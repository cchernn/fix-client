import quickfix
import time
import datetime
import random

from helpers import parse_fix_message, setup_logger, log

class fix_pricing(quickfix.Application):
    def __init__(self, session, start_timestamp=datetime.datetime.utcnow()):
        super().__init__()
        self.logger = setup_logger(
            name="logger",
            log_file=f"Log/{start_timestamp}.log",
            format_str='%(asctime)s %(levelname)s %(message)s'
        )
        self.session = session
        self.sessionID = None
        self.connected = False

        self.order_index = 0

        self._Market_Data = []
        self._Market_Orders = {}

    #####################################################
    # QuickFIX Application Methods

    def onCreate(self, sessionID):
        """
        Called when application is initialized
        """
        self.sessionID = sessionID
        log(self.logger, f"[onCreate] Application created with sessionID = {sessionID}")

    def onLogon(self, sessionID):
        """
        Called on session logOn
        """
        log(self.logger, "[onLogon] Logon Successful")
        self.connected = True

    def onLogout(self, sessionID):
        """
        Called on session logOut
        """
        log(self.logger, "[onLogout] Logout Successful")
        self.connected = False

    def onMessage(self, message, sessionID):
        log(self.logger, f"[onMessage] Message = {parse_fix_message(message)}")

    def toAdmin(self, message, sessionID):
        """
        Process outgoing session-level messages (logon, logout, heartbeat) before they are sent
        """
        log(self.logger, f"[toAdmin] {parse_fix_message(message)}")

        msgType = quickfix.MsgType()
        message.getHeader().getField(msgType)

        if (msgType.getValue() == quickfix.MsgType_Logon): 
            log(self.logger, f"[toAdmin] Sending LogOn Request")

        elif (msgType.getValue() == quickfix.MsgType_Logout): 
            log(self.logger, f"[toAdmin] Sending LogOut Request")
        
        elif (msgType.getValue() == quickfix.MsgType_Heartbeat):
            log(self.logger, f"[toAdmin] Sending Heartbeat")
        
        return
    
    def fromAdmin(self, message, sessionID):
        """
        Process incoming session-level messages (logon, logout, heartbeat)
        """
        log(self.logger, f"[fromAdmin] {parse_fix_message(message)}")

        msgType = quickfix.MsgType()
        message.getHeader().getField(msgType)

        if (msgType.getValue() == quickfix.MsgType_Logon): 
            log(self.logger, f"[fromAdmin] Logon Successful")

        elif (msgType.getValue() == quickfix.MsgType_Logout): 
            log(self.logger, f"[fromAdmin] Logout Successful")
        
        elif (msgType.getValue() == quickfix.MsgType_Heartbeat):
            log(self.logger, f"[fromAdmin] Heartbeat Successful")

        ### Process Reject messages (tag 35=3)
        elif (msgType.getValue() == quickfix.MsgType_Reject):
            ClOrdID = quickfix.ClOrdID() #11
            Text = quickfix.Text() #58
            RefSeqNum = quickfix.RefSeqNum() #45
            RefTagID = quickfix.RefTagID() #371
            RefMsgType = quickfix.RefMsgType() #372
            SessionRejectReason = quickfix.SessionRejectReason() #373

            ### Get SendingTime (tag 52)
            sendingTime = quickfix.SendingTime()
            message.getHeader().getField(sendingTime)
            sendingTime = sendingTime.getString()

            ### Get MsgSeqNum (tag 34)
            msgSeqNum = quickfix.MsgSeqNum()
            message.getHeader().getField(msgSeqNum)
            msgSeqNum = msgSeqNum.getValue()

            _market_data_update = {
                'type': "receive",
                '35': msgType,
                '52': sendingTime,
                '34': msgSeqNum,
            }
    
            for metric in [ClOrdID, Text, RefSeqNum, RefTagID, RefMsgType, SessionRejectReason]:
                if message.isSetField(metric):
                    message.getField(metric)
                    _market_data_update.update({
                        str(metric.getField()): metric.getValue()
                    })

            self._Market_Data.append(_market_data_update)

            log(self.logger, f"Received Reject for ClOrdID {ClOrdID.getValue()} with Reason {Text}", level="DEBUG")
        
        return
    
    def toApp(self, message, sessionID):
        """
        Process outgoing application-level messages before they are sent.
        """
        log(self.logger, f"[toApp] {parse_fix_message(message)}")

    def fromApp(self, message, sessionID):
        """
        Handle incoming application-level messages.
        """
        log(self.logger, f"[fromApp] {parse_fix_message(message)}")

        ### Get MsgType (tag 35)
        msgType = quickfix.MsgType()
        message.getHeader().getField(msgType)
        msgType = msgType.getValue()
        
        ### Get SendingTime (tag 52)
        sendingTime = quickfix.SendingTime()
        message.getHeader().getField(sendingTime)
        sendingTime = sendingTime.getString()

        ### Get MsgSeqNum (tag 34)
        msgSeqNum = quickfix.MsgSeqNum()
        message.getHeader().getField(msgSeqNum)
        msgSeqNum = msgSeqNum.getValue()

        # Process ExecutionReport messages (tag 35=8)
        if msgType == quickfix.MsgType_ExecutionReport:
            ClOrdID = quickfix.ClOrdID() #11
            OrdStatus = quickfix.OrdStatus() #39
            ExecType = quickfix.ExecType() #150
            OrderID = quickfix.OrderID() #37
            Side = quickfix.Side() #54
            Symbol = quickfix.Symbol() #55
            OrdType = quickfix.OrdType() #40
            Text = quickfix.Text() #58

            OrderQty = quickfix.OrderQty() #38
            Price = quickfix.Price() #44
            LastPx = quickfix.LastPx() #31
            LastShares = quickfix.LastShares() #32

            _market_data_update = {
                'type': "receive",
                '35': msgType,
                '52': sendingTime,
                '34': msgSeqNum,
            }
    
            for metric in [ClOrdID, OrdStatus, ExecType, OrderID, Side, Symbol, OrdType, Text, OrderQty, Price, LastPx, LastShares]:
                if message.isSetField(metric):
                    message.getField(metric)
                    _market_data_update.update({
                        str(metric.getField()): metric.getValue()
                    })

            self._Market_Data.append(_market_data_update)

            if (ClOrdID.getValue() in self._Market_Orders):
                if ('37' not in self._Market_Orders[ClOrdID.getValue()]):
                    self._Market_Orders[ClOrdID.getValue()].update({'37': OrderID.getValue()})

            log(self.logger, f"[fromApp] Received ExecutionReport for ClOrdID {ClOrdID.getValue()} with Order Status {OrdStatus.getValue()}", level="DEBUG")
       
        # Process OrderCancelReject messages (tag 35=9)
        if msgType == quickfix.MsgType_OrderCancelReject:
            ClOrdID = quickfix.ClOrdID() #11
            OrderID = quickfix.OrderID() #37
            OrdStatus = quickfix.OrdStatus() #39
            OrigClOrdID = quickfix.OrigClOrdID() #41
            Text = quickfix.Text() #58

            _market_data_update = {
                'type': "receive",
                '35': msgType,
                '52': sendingTime,
                '34': msgSeqNum,
            }
    
            for metric in [ClOrdID, OrdStatus, OrderID, Text, OrigClOrdID]:
                if message.isSetField(metric):
                    message.getField(metric)
                    _market_data_update.update({
                        str(metric.getField()): metric.getValue()
                    })

            self._Market_Data.append(_market_data_update)

            log(self.logger, f"[fromApp] Received OrderCancelReject for ClOrdID {ClOrdID.getValue()} with Reason {Text}", level="DEBUG")
        
        return

    #####################################################
    def genClOrdID(self):
        """
        Generate clOrdID
        """
        self.order_index += 1
        clOrdID = f"{self.order_index:08d}"
        return clOrdID

    #####################################################
    def sendNewOrderSingle(self, side, symbol, orderqty, price, ordtype, handl_inst):
        """
        Create New Order (tag 35=D)
        """
        message = quickfix.Message()
        header = message.getHeader()

        header.setField(quickfix.MsgType(quickfix.MsgType_NewOrderSingle))
        
        ClOrdID = self.genClOrdID()
        now = datetime.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
        # Set unique cl0rdID for this request
        message.setField(quickfix.ClOrdID(ClOrdID)) #11
        message.setField(quickfix.Side(side)) #54 = 1 BUY 
        message.setField(quickfix.Symbol(symbol)) #55 = MSFT
        message.setField(quickfix.OrderQty(orderqty)) #38 = 1000
        if ordtype == "2":
            message.setField(quickfix.Price(price)) #44 only if ordtype=2, Limit Order
        message.setField(quickfix.OrdType(ordtype)) #40=2 Limit Order 
        message.setField(quickfix.HandlInst(handl_inst)) #21 = 3
        message.setField(quickfix.TimeInForce('0')) #59
        message.setField(quickfix.Text("NewOrderSingle")) #58
        trstime = quickfix.TransactTime()
        trstime.setString(now)
        message.setField(trstime)

        self.session.sendToTarget(message, self.sessionID)

        log(self.logger, f"[sendNewOrderSingle] {ClOrdID}: New Order for {symbol}", level="DEBUG")

        _new_order = {
            "type": "send",
            "11": ClOrdID, #ClOrdID
            "54": side, #Side
            "55": symbol, #Symbol
            "38": orderqty, #OrderQty
            "44": price, #Price
            "40": ordtype, #OrdType
            "58": "NewOrderSingle", #Text
            "60": now, #TransactTime
        }
        self._Market_Data.append(_new_order)

        self._Market_Orders[ClOrdID] = _new_order

    #####################################################
    def sendOrderCancelRequest(self, origClOrdID):
        """
        Cancel Order (tag 35=F)
        """
        message = quickfix.Message()
        header = message.getHeader()

        header.setField(quickfix.MsgType(quickfix.MsgType_OrderCancelRequest))
        
        order_details = self._Market_Orders[origClOrdID]
        side = order_details['54']
        symbol = order_details['55']
        trstime = order_details['60']
        orderID = order_details['37'] if '37' in order_details else None

        ClOrdID = self.genClOrdID()
        # Set unique cl0rdID for this request
        message.setField(quickfix.ClOrdID(ClOrdID)) #11
        message.setField(quickfix.OrigClOrdID(origClOrdID)) #41
        message.setField(quickfix.Side(side)) #54 = 1 BUY 
        message.setField(quickfix.Symbol(symbol)) #55 = MSFT
        _trstime = quickfix.TransactTime()
        _trstime.setString(trstime)
        message.setField(_trstime) #60
        message.setField(quickfix.Text("OrderCancelRequest")) # 58
        if orderID:
            message.setField(quickfix.OrderID(orderID)) #37

        self.session.sendToTarget(message, self.sessionID)

        log(self.logger, f"[sendOrderCancelRequest] {ClOrdID}: Cancel Order for {origClOrdID}", level="DEBUG")

        _cancel_order = {
            "type": "send",
            "11": ClOrdID, #ClOrdID
            "54": side, #Side
            "55": symbol, #Symbol
            "41": origClOrdID, #OrigClOrdID
            "58": "OrderCancelRequest", #Text
            "60": trstime, #TransactTime
        }
        if orderID:
            _cancel_order.update({
                "37": orderID, #OrderID
            })
        self._Market_Data.append(_cancel_order)

    #####################################################
    def run(self):
        """
        Execute simulation
        Run 1000 new order requests and cancel some orders subsequently
        """
        time.sleep(2) ### buffer 2sec for login

        ### Declare new order options for randomization
        side_options = ["1", "2", "3"]
        side_options_weights = [0.4, 0.3, 0.3]
        symbols = ["MSFT", "BAC", "AAPL"]
        range_orderqty = (1, 10000)
        range_price = {
            "MSFT": (100, 400),
            "BAC": (0, 100),
            "AAPL": (100, 300)
        }
        ordtypes = ["1", "2"]
        handl_insts = ["1", "2"]

        ### Set number of iterations (default: 1000) and cancel_probability (default: 0.05) to determine odds of sending cancel order
        iterations = 1000 #1000
        cancel_probability = 0.05 #0.05
        
        ### Begin Simulation
        start_time = time.time()
        for _ in range(0, iterations):
            ### Send New Orders
            symbol_choice = random.choice(symbols)
            range_price_choice = range_price[symbol_choice]
            self.sendNewOrderSingle(
                side=random.choices(side_options, weights=side_options_weights)[0], # 1=quickfix.Side_BUY, 2=quickfix.Side_SELL, 3=quickfix.Side_SELL_SHORT
                symbol=symbol_choice, 
                orderqty=random.randint(range_orderqty[0], range_orderqty[1]), 
                price=random.randint(range_price_choice[0], range_price_choice[1]), 
                ordtype=random.choice(ordtypes), # 1=quickfix.OrdType_MARKET, 2=quickfix.OrdType_LIMIT
                handl_inst=random.choice(handl_insts) # 1=quickfix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE_NO_BROKER_INTERVENTION, 2=quickfix.HandlInst_AUTOMATED_EXECUTION_ORDER_PUBLIC_BROKER_INTERVENTION_OK, 3=quickfix.HandlInst_MANUAL_ORDER_BEST_EXECUTION
            )
            ### Send Cancel Orders if P < cancel_probability
            if (len(self._Market_Orders) > 0) and (random.random() <= cancel_probability):
                order_choice = random.choice(list(self._Market_Orders.keys()))
                self.sendOrderCancelRequest(origClOrdID=order_choice)
        
        ### End Simulation
        time.sleep(10) ### buffer 10sec for remaining transactions
        
        ### Summarize runtime
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        log(self.logger, f"Simulation Complete, Time Taken {minutes:02}:{seconds:02}", _print=True)
