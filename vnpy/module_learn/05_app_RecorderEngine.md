# app engine
主引擎自带的三个引擎是同样类型

## RecorderEngine

### RecorderEngine 主要数据流
主要用于传输TickData/BarData

#### 数据流
1. 利用EventTick：将数据保存自类ticks列表中。
   1. tick_recordings/bar_recordings:筛选器
2. 利用定时事件：将ticks中的数据压入队列queue
3. 分线程不断从queue中取出数据，执行入库操作


注意：
- 第二步，queue中每个元素只保存一个tickdata。
- 由上，第三步是逐个元素入库。
- 此处是明显的效率瓶颈。

#### 驱动来源
event_engine中的EVENT_TICK/EVENT_TIMER
回调处理函数由事件引擎驱动。

### RecorderEngine 初始化步骤
``` python
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)
        #<1>:队列和线程
        self.queue: Queue = Queue()
        self.thread: Thread = Thread(target=self.run) #<2>:线程启动
        self.active: bool = False

        self.tick_recordings: Dict[str, Dict] = {}
        self.bar_recordings: Dict[str, Dict] = {}
        self.bar_generators: Dict[str, BarGenerator] = {}

        self.timer_count: int = 0
        self.timer_interval: int = 10

        self.ticks: Dict[str, List[TickData]] = defaultdict(list)
        self.bars: Dict[str, List[BarData]] = defaultdict(list)
        # <3> 数据库
        self.database: BaseDatabase = get_database()
        # <4> 加载配置文件
        self.load_setting() # <>更新self.tick_recordings/self.bar_recordings，字典结构
        # <5> 注册处理事件函数
        self.register_event()
        # <6> 入库线程启动
        self.start()
        # <7> 界面更新事件？
        self.put_event() # 这个函数到底是用来干嘛的？
```
#### <2> 线程入口函数指定
存储数据在这个线程中进行，这个线程其实也是一个事件驱动的引擎。
queue中的data被不断的取出，然后放入到database接口中进行存储。
``` python
# self.thread: Thread = Thread(target=self.run) #<>:线程启动
    def run(self) -> None:
        """"""
        while self.active:
            try:
                task: Any = self.queue.get(timeout=1)
                task_type, data = task

                if task_type == "tick":
                    self.database.save_tick_data(data)
                elif task_type == "bar":
                    self.database.save_bar_data(data)

            except Empty:
                continue

            except Exception:
                self.active = False

                info = sys.exc_info()
                event: Event = Event(EVENT_RECORDER_EXCEPTION, info)
                self.event_engine.put(event)
```

#### <3> 数据库
数据库默认使用的是sqllite，在SETTINGS中设置。

#### <4> 读取配置文件

self.setting_filename: str = "data_recorder_setting.json"

``` python load_setting
    def load_setting(self) -> None:
        """"""
        setting: dict = load_json(self.setting_filename) #<4.1>
        self.tick_recordings = setting.get("tick", {})
        self.bar_recordings = setting.get("bar", {})
```

没有配置文件的化，返回两个空字典。这两个字典是干嘛的？

``` python load_json
# from vnpy.trader.utility import load_json

def load_json(filename: str) -> dict:
    """
    Load data from json file in temp path.
    """
    filepath = get_file_path(filename)

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            data = json.load(f)
        return data
    else:
        save_json(filename, {})
        return {}
```

#### <5> 注册Event处理函数

``` python
    # 在事件引擎中，注册四个处理函数。
    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_TIMER, self.process_timer_event) #<5.1>
        self.event_engine.register(EVENT_TICK,  self.process_tick_event)   #<5.2>
        self.event_engine.register(EVENT_CONTRACT,    self.process_contract_event) #<5.3>
        self.event_engine.register(EVENT_SPREAD_DATA, self.process_spread_event) #<5.4>
```

##### <5.1> 引擎内部定时处理：process_timer_event


这个队列不是事件引擎的，而是appengine自带的。
1. app使用定时器计算定时时间，调用process_timer_event
   1. timer_count：由EVENT_TICK事件回调+1
   2. timer_count加到timer_interval时进行process_timer_event实际调用
2. process_timer_event将"bar"/"tick"事件入列（put)，这个事件仅在appengine中使用
3. bars/ticks清除。
4. bars/ticks是保存有barData、TickData的字典列表。

``` python
    def process_timer_event(self, event: Event) -> None:
        """"""
        self.timer_count += 1
        if self.timer_count < self.timer_interval:
            return
        self.timer_count = 0

        for bars in self.bars.values(): # bars是一个字典结构
            self.queue.put(("bar", bars)) # 队列里放着bar，tick两类数据
        self.bars.clear()

        for ticks in self.ticks.values():
            self.queue.put(("tick", ticks))
        self.ticks.clear()
```

##### <5.2> 处理tick事件

``` python
    def process_tick_event(self, event: Event) -> None:
        """"""
        tick: TickData = event.data
        self.update_tick(tick)
```

###### 处理tick事件的步骤
``` python
    def update_tick(self, tick: TickData) -> None:
        """"""
        if tick.vt_symbol in self.tick_recordings:
            self.record_tick(copy(tick)) # ticks对应的list中添加当前tickdata

        if tick.vt_symbol in self.bar_recordings:
            bg: BarGenerator = self.get_bar_generator(tick.vt_symbol)
            bg.update_tick(copy(tick)) #根据当前的tick来确定是否需要更新bar
```
###### 记录tick
``` python
    def record_tick(self, tick: TickData) -> None:
        """"""
        self.ticks[tick.vt_symbol].append(tick)
```


###### BarGenerator 类
这个类很重要，这个类中只包含一个Bardata？
``` python
    def get_bar_generator(self, vt_symbol: str) -> BarGenerator:
        """"""
        bg: BarGenerator = self.bar_generators.get(vt_symbol, None) 

        if not bg:
            bg: BarGenerator = BarGenerator(self.record_bar)
            self.bar_generators[vt_symbol] = bg

        return bg
```

``` python bg.update_tick
    def update_tick(self, tick: TickData) -> None:
        """
        Update new tick data into generator.
        """
        new_minute = False

        # Filter tick data with 0 last price
        if not tick.last_price:
            return

        # Filter tick data with older timestamp
        if self.last_tick and tick.datetime < self.last_tick.datetime:
            return

        if not self.bar:
            new_minute = True
        elif (
            (self.bar.datetime.minute != tick.datetime.minute)
            or (self.bar.datetime.hour != tick.datetime.hour)
        ):
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
        else:
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            if tick.high_price > self.last_tick.high_price:
                self.bar.high_price = max(self.bar.high_price, tick.high_price)

            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            if tick.low_price < self.last_tick.low_price:
                self.bar.low_price = min(self.bar.low_price, tick.low_price)

            self.bar.close_price = tick.last_price
            self.bar.open_interest = tick.open_interest
            self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

            turnover_change = tick.turnover - self.last_tick.turnover
            self.bar.turnover += max(turnover_change, 0)

        self.last_tick = tick
```

##### <5.3> process_contract_event
contract_event:主要启动订阅操作。

``` python 
    def process_contract_event(self, event: Event) -> None:
        """"""
        contract: ContractData = event.data
        vt_symbol: str = contract.vt_symbol

        if (vt_symbol in self.tick_recordings or vt_symbol in self.bar_recordings):
            self.subscribe(contract)
```

``` python 
    def subscribe(self, contract: ContractData) -> None:
        """"""
        req: SubscribeRequest = SubscribeRequest(
            symbol=contract.symbol,
            exchange=contract.exchange
        )
        self.main_engine.subscribe(req, contract.gateway_name)
```

#### <6> 线程启动

``` python

    def start(self) -> None:
        """"""
        self.active = True
        self.thread.start()
```

#### <7> 界面更新事件？
EVENT_RECORDER_UPDATE事件，这个事件的处理函数在界面
这个是干嘛的？
``` python put_event

    def put_event(self) -> None:
        """"""
        tick_symbols: List[str] = list(self.tick_recordings.keys())
        tick_symbols.sort()

        bar_symbols: List[str] = list(self.bar_recordings.keys())
        bar_symbols.sort()

        data: dict = {
            "tick": tick_symbols,
            "bar": bar_symbols
        }

        event: Event = Event(
            EVENT_RECORDER_UPDATE,
            data
        )
        self.event_engine.put(event)
```



### RecorderEngine中的queue

#### queue中保存的内容

保存两个内容：bar数据和tick数据
self.ticks: Dict[str, List[TickData]] = defaultdict(list)
self.bars: Dict[str, List[BarData]] = defaultdict(list)

``` python

    def process_timer_event(self, event: Event) -> None:
        """"""
        self.timer_count += 1
        if self.timer_count < self.timer_interval:
            return
        self.timer_count = 0

        for bars in self.bars.values():
            self.queue.put(("bar", bars))
        self.bars.clear()

        for ticks in self.ticks.values():
            self.queue.put(("tick", ticks))
        self.ticks.clear()
```


#### queue取出操作在appEngine的run线程中
该线程专门用于queue出列，根据事件
1. tick: database.save_tick_data(data)
2. bar: database.save_bar_data(data)

``` python

    def run(self) -> None:
        """"""
        while self.active:
            try:
                task: Any = self.queue.get(timeout=1)
                task_type, data = task

                if task_type == "tick":
                    self.database.save_tick_data(data)
                elif task_type == "bar":
                    self.database.save_bar_data(data)

            except Empty:
                continue

            except Exception:
                self.active = False

                info = sys.exc_info()
                event: Event = Event(EVENT_RECORDER_EXCEPTION, info)
                self.event_engine.put(event)
```


### RecorderEngine中的数据结构


#### RecorderEngine.tick_recordings

这个数据结构中存的是什么东西？用来筛选需要记录的合约数据，如果不再集合内，就pass。
self.tick_recordings: Dict[str, Dict] = {}
self.bar_recordings: Dict[str, Dict] = {}

##### 存档 读档
``` python
    def load_setting(self) -> None:
        """"""
        setting: dict = load_json(self.setting_filename)
        self.tick_recordings = setting.get("tick", {})
        self.bar_recordings = setting.get("bar", {})

    def save_setting(self) -> None:
        """"""
        setting: dict = {
            "tick": self.tick_recordings,
            "bar": self.bar_recordings
        }
        save_json(self.setting_filename, setting)
```

##### 添加删除

``` python

    def add_tick_recording(self, vt_symbol: str) -> None:
        """"""
        if vt_symbol in self.tick_recordings:
            self.write_log(f"已在Tick记录列表中：{vt_symbol}")
            return

        # For normal contract
        if Exchange.LOCAL.value not in vt_symbol:
            contract: ContractData = self.main_engine.get_contract(vt_symbol)
            if not contract:
                self.write_log(f"找不到合约：{vt_symbol}")
                return

            self.tick_recordings[vt_symbol] = {
                "symbol": contract.symbol,
                "exchange": contract.exchange.value,
                "gateway_name": contract.gateway_name
            }

            self.subscribe(contract)
        # No need to subscribe for spread data
        else:
            self.tick_recordings[vt_symbol] = {}

        self.save_setting()
        self.put_event()

        self.write_log(f"添加Tick记录成功：{vt_symbol}")

    def remove_tick_recording(self, vt_symbol: str) -> None:
        """"""
        if vt_symbol not in self.tick_recordings:
            self.write_log(f"不在Tick记录列表中：{vt_symbol}")
            return

        self.tick_recordings.pop(vt_symbol)
        self.save_setting()
        self.put_event()

        self.write_log(f"移除Tick记录成功：{vt_symbol}")

```


#### RecorderEngine.bar_recordings


##### 存档读档
与上一节一样

##### 添加删除
``` python

    def add_bar_recording(self, vt_symbol: str) -> None:
        """"""
        if vt_symbol in self.bar_recordings:
            self.write_log(f"已在K线记录列表中：{vt_symbol}")
            return

        if Exchange.LOCAL.value not in vt_symbol:
            contract: ContractData = self.main_engine.get_contract(vt_symbol)
            if not contract:
                self.write_log(f"找不到合约：{vt_symbol}")
                return

            self.bar_recordings[vt_symbol] = {
                "symbol": contract.symbol,
                "exchange": contract.exchange.value,
                "gateway_name": contract.gateway_name
            }

            self.subscribe(contract)
        else:
            self.bar_recordings[vt_symbol] = {}

        self.save_setting()
        self.put_event()

        self.write_log(f"添加K线记录成功：{vt_symbol}")

    def remove_bar_recording(self, vt_symbol: str) -> None:
        """"""
        if vt_symbol not in self.bar_recordings:
            self.write_log(f"不在K线记录列表中：{vt_symbol}")
            return

        self.bar_recordings.pop(vt_symbol)
        self.save_setting()
        self.put_event()

        self.write_log(f"移除K线记录成功：{vt_symbol}")

```


#### RecorderEngine.ticks/bars
这个应该直接存储ticks和bars的数据list

##### tick/bars入库操作
``` python

    def process_timer_event(self, event: Event) -> None:

        """"""
        self.timer_count += 1
        if self.timer_count < self.timer_interval:
            return
        self.timer_count = 0

        for bars in self.bars.values():
            self.queue.put(("bar", bars))
        self.bars.clear()

        for ticks in self.ticks.values():
            self.queue.put(("tick", ticks))
        self.ticks.clear()


    def run(self) -> None:
        """"""
        while self.active:
            try:
                task: Any = self.queue.get(timeout=1)
                task_type, data = task

                if task_type == "tick":
                    self.database.save_tick_data(data)
                elif task_type == "bar":
                    self.database.save_bar_data(data)
        。。。。。
```

##### app内部更新ticks/bars
``` python

# 在TICK事件出栈时，这些函数被依次调用。
    def process_tick_event(self, event: Event) -> None:
        """"""
        tick: TickData = event.data
        self.update_tick(tick)
    
    def update_tick(self, tick: TickData) -> None:
        """"""
        if tick.vt_symbol in self.tick_recordings:
            self.record_tick(copy(tick))

        if tick.vt_symbol in self.bar_recordings:
            bg: BarGenerator = self.get_bar_generator(tick.vt_symbol)
            bg.update_tick(copy(tick))

    def record_tick(self, tick: TickData) -> None:
        """"""
        self.ticks[tick.vt_symbol].append(tick)

    def record_bar(self, bar: BarData) -> None:
        """"""
        self.bars[bar.vt_symbol].append(bar)

    def record_bar(self, bar: BarData) -> None:
        """"""
        self.bars[bar.vt_symbol].append(bar)

    def get_bar_generator(self, vt_symbol: str) -> BarGenerator:
        """"""
        bg: BarGenerator = self.bar_generators.get(vt_symbol, None)

        if not bg:
            bg: BarGenerator = BarGenerator(self.record_bar)
            self.bar_generators[vt_symbol] = bg

        return bg

```



##