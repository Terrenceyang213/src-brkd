# app - BacktestingEngine
回测类
> ./backtesting.py
> ./base.py
> ./engine.py
> ./template.py
> ./stategies/boll_channel_strategy.py
> ./stategies/double_ma_strategy.py
> ./stategies/dual_thrust_strategy.py
> ./stategies/king_keltner_strategy.py
> ./stategies/multi_signal_strategy.py
> ./stategies/multi_timeframe_strategy.py
> ./stategies/test_strategy.py
> ./stategies/turtle_signal_strategy.py

## BacktestingEngine概述
1. 回测数据在这个引擎中组织
2. 这个引擎中没有队列，通过模拟BarData来调用策略中的回调on_bar/on_tick
   1. 没有队列，那么put，pop操作应该是没有。
   2. 

## BacktestingEngine的使用步骤
这个类的初始化只涉及一些数据相关的字段，没有控制流的信息。其使用在`BacktesterEngine.run_backtesting()`方法中

### 测试器源代码
``` py class BacktesterEngine:
    def run_backtesting(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        inverse: bool,
        setting: dict
    ):
        """"""
        self.result_df = None
        self.result_statistics = None

        engine = self.backtesting_engine # <1>
        engine.clear_data() # <2>

        if interval == Interval.TICK.value:
            mode = BacktestingMode.TICK
        else:
            mode = BacktestingMode.BAR

        engine.set_parameters(
            vt_symbol=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital,
            inverse=inverse,
            mode=mode
        ) # <3>

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            setting
        ) # <4>

        engine.load_data() # <5>

        try:
            engine.run_backtesting() # <6>
        except Exception:
            msg = f"策略回测失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

            self.thread = None
            return

        self.result_df = engine.calculate_result() # <7>
        self.result_statistics = engine.calculate_statistics(output=False) # <8>

        # Clear thread object handler.
        self.thread = None # <9>

        # Put backtesting done event
        event = Event(EVENT_BACKTESTER_BACKTESTING_FINISHED)
        self.event_engine.put(event) # <10>
```

### 测试器中体现的backtestingEngine启动步骤
1. engine = self.backtesting_engine： 这个就是BacktestingEngine()
2. engine.clear_data()：清除数据
3. engine.set_parameters(...): 设置引擎参数
   1. vt_symbol:str类型，交易品种，只对应一只
   2. interval:间隔参数，tick，分钟，小时
   3. start/end:起止时间
   4. rate：？
   5. slippage:滑点
   6. size:?
   7. pricetick：？
   8. capital：投资资本
   9. inverse？
   10. mode：tick/Bar
4. **engine.add_strategy(strategy_class, setting)**
    1.  strategy_class = self.classes[class_name]
    2.  engine.add_strategy：将策略添加到引擎中。
5. engine.load_data() ： 加载数据
6. **engine.run_backtesting()**：运行回测
7. self.result_df = engine.calculate_result()：计算结果
8. self.result_statistics = engine.calculate_statistics(output=False)：统计结果
9. **self.thread = None** ：线程清理，再次之前应该要等待线程结束吧。
10. self.event_engine.put(event) : 回测结束事件入列。

### 4. add_strategy
这个函数主要是在函数中将strategy通过传入的class实例化。
``` py add_strategy

    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(
            self, strategy_class.__name__, self.vt_symbol, setting
        )
```

### 5. load_data()
``` py
    def load_data(self):
        """"""
        self.output("开始加载历史数据")

        if not self.end:
            self.end = datetime.now()

        if self.start >= self.end:
            self.output("起始日期必须小于结束日期")
            return

        self.history_data.clear()       # Clear previously loaded history data

        # Load 30 days of data each time and allow for progress update
        total_days = (self.end - self.start).days
        progress_days = max(int(total_days / 10), 1)
        progress_delta = timedelta(days=progress_days)
        interval_delta = INTERVAL_DELTA_MAP[self.interval]

        start = self.start
        end = self.start + progress_delta
        progress = 0

        while start < self.end:
            progress_bar = "#" * int(progress * 10 + 1)
            self.output(f"加载进度：{progress_bar} [{progress:.0%}]")

            end = min(end, self.end)  # Make sure end time stays within set range

            if self.mode == BacktestingMode.BAR:
                data = load_bar_data(
                    self.symbol,
                    self.exchange,
                    self.interval,
                    start,
                    end
                )
            else:
                data = load_tick_data(
                    self.symbol,
                    self.exchange,
                    start,
                    end
                )

            self.history_data.extend(data)

            progress += progress_days / total_days
            progress = min(progress, 1)

            start = end + interval_delta
            end += progress_delta

        self.output(f"历史数据加载完成，数据量：{len(self.history_data)}")

```

### 6. run_backtesting
引擎回测主体逻辑涉及
1. Strategy类
2. BarGenerator
3. ArrayManager
4. historydata

``` py run_backtesting
    def run_backtesting(self):
        """"""
        # <6.1>
        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        else:
            func = self.new_tick

        self.strategy.on_init()

        # <6.2>
        # Use the first [days] of history data for initializing strategy
        day_count = 0
        ix = 0

        for ix, data in enumerate(self.history_data):
            if self.datetime and data.datetime.day != self.datetime.day:
                day_count += 1
                if day_count >= self.days:
                    break

            self.datetime = data.datetime

            try:
                self.callback(data)
            except Exception:
                self.output("触发异常，回测终止")
                self.output(traceback.format_exc())
                return

        # <6.3>
        self.strategy.inited = True
        self.output("策略初始化完成")

        self.strategy.on_start()
        self.strategy.trading = True
        self.output("开始回放历史数据")

        # Use the rest of history data for running backtesting
        backtesting_data = self.history_data[ix:]
        if len(backtesting_data) <= 1:
            self.output("历史数据不足，回测终止")
            return

        total_size = len(backtesting_data)
        batch_size = max(int(total_size / 10), 1)

        # <6.4>
        for ix, i in enumerate(range(0, total_size, batch_size)):
            batch_data = backtesting_data[i: i + batch_size]
            for data in batch_data:
                try:
                    func(data)
                except Exception:
                    self.output("触发异常，回测终止")
                    self.output(traceback.format_exc())
                    return

            progress = min(ix / 10, 1)
            progress_bar = "=" * (ix + 1)
            self.output(f"回放进度：{progress_bar} [{progress:.0%}]")

        self.strategy.on_stop()
        self.output("历史数据回放结束")
```

#### 6.1 mode/new_bar/new_tick
func在这步根据mode确定接下来，是出发新bar事件，还是tick事件。
backtesting引擎使用这个函数来直接调用策略的on_bar/on_tick事件。
其实是一种对事件驱动的模拟。

``` py 
        # <6.1>
        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        else:
            func = self.new_tick

        self.strategy.on_init()
```

``` py
    def new_bar(self, bar: BarData):
        """"""
        self.bar = bar
        self.datetime = bar.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_bar(bar) # 通过新传进来的数据，调用策略的on_bar
        self.update_daily_close(bar.close_price)

    def new_tick(self, tick: TickData):
        """"""
        self.tick = tick
        self.datetime = tick.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_tick(tick) # 通过新传进来的数据，调用策略的on_tick

        self.update_daily_close(tick.last_price)
```

#### 6.2 history_data/callback
1. history_data是一个list，在load_data函数中处理。
2. callback是外部传递进来的可调用对象,在以下几个函数中被传入:
   1. load_bar/load_tick
   2. 在backtesting内部并未被调用。
   3. 在CtaTemplate(strategy基类)的load_bar里面初始化：callback = self.on_bar
3. 这部分很可能在`break`跳出,只能这么解释，因为callback根本没初始化。

这里到底想干什么？计算history_data的数据量day_count要大于self.days？
``` py
        # <2>
        # Use the first [days] of history data for initializing strategy
        day_count = 0
        ix = 0

        for ix, data in enumerate(self.history_data):
            if self.datetime and data.datetime.day != self.datetime.day:
                day_count += 1
                if day_count >= self.days:
                    break

            self.datetime = data.datetime

            try:
                self.callback(data) # strategy对象中的on_bar
            except Exception:
                self.output("触发异常，回测终止")
                self.output(traceback.format_exc())
                return
```

#### 6.3 strategy初始化

``` py strategy
        # <6.1>
        self.strategy.on_init()
        ....
        # <6.3>
        self.strategy.inited = True
        self.output("策略初始化完成")

        self.strategy.on_start()
        self.strategy.trading = True
        self.output("开始回放历史数据")
```

BollChannelStrategy为例
``` py BollChannelStrategy.on_init

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

```

``` py CtaTemplate.load_bar
    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
        use_database: bool = False
    ):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar

        self.cta_engine.load_bar( #cta_engine是backtestingEngine
            self.vt_symbol,
            days,
            interval,
            callback,
            use_database
        )
```

``` py BollChannelStrategy.on_start

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
```


#### 6.4 回测主体
``` py backtesting body
        # <6.4>
        for ix, i in enumerate(range(0, total_size, batch_size)):
            batch_data = backtesting_data[i: i + batch_size]
            for data in batch_data:
                try:
                    func(data) # new_bar模拟产生数据，调用strategy里面的on_bar回调
                except Exception:
                    self.output("触发异常，回测终止")
                    self.output(traceback.format_exc())
                    return

            progress = min(ix / 10, 1)
            progress_bar = "=" * (ix + 1)
            self.output(f"回放进度：{progress_bar} [{progress:.0%}]")

        self.strategy.on_stop()
        self.output("历史数据回放结束")
```

``` py BollChannelStrategy.on_bar
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar) 
        # self.bg = BarGenerator(self.on_bar        # on_bar
        #                       , 15                # window
        #                       , self.on_15min_bar # on_window_bar
        #                       )
```

在`update_bar_minute_window/update_bar_hour_window`中调用的`on_window_bar`是策略的核心判断逻辑
``` py BarGenerator.update_bar
    # 根据BarData更新K线数据
    def update_bar(self, bar: BarData) -> None:
        """
        Update 1 minute bar into generator
        """
        if self.interval == Interval.MINUTE:
            self.update_bar_minute_window(bar) #<>
        else:
            self.update_bar_hour_window(bar) #<>
```

**宝林线回测策略主体**
这个策略逻辑主体必须在BarGenerator的初始化里面注册才能生效。

``` py BollChannelStrategy.on_15min_bar
    # self.bg = BarGenerator(self.on_bar        # on_bar
    #                       , 15                # window
    #                       , self.on_15min_bar # on_window_bar
    #                       )
    def on_15min_bar(self, bar: BarData):
        """"""
        self.cancel_all() # 调用到的是cta_engine.cancel_all(self)

        am = self.am
        am.update_bar(bar) # 更新barData时间序列ArrayManager,这个是计算指标的主体
        if not am.inited:
            return

        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev) #宝林线
        self.cci_value = am.cci(self.cci_window) #cci
        self.atr_value = am.atr(self.atr_window) #atr
        # 仓位为0
        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            #买卖信号
            if self.cci_value > 0:
                self.buy(self.boll_up, self.fixed_size, True)
            elif self.cci_value < 0:
                self.short(self.boll_down, self.fixed_size, True)

        # 仓位为正：调仓信号，直接调？不判断？
        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.long_stop = self.intra_trade_high - self.atr_value * self.sl_multiplier
            self.sell(self.long_stop, abs(self.pos), True)
        # 仓位为负：调仓信号
        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            self.short_stop = self.intra_trade_low + self.atr_value * self.sl_multiplier
            self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()
```


### 关键数据结构
1. 回测数据：history_data
   1. 
2. 策略：
   1. strategy_class
   2. strategy
3. 配置参数：
   1. 