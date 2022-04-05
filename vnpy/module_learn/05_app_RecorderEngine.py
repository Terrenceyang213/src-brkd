#%% 直接使用DataRecorder

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.setting import SETTINGS
from logging import INFO
from vnpy.app.data_recorder import RecorderEngine
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange
import time
from vnpy.trader.event import EVENT_TICK

from quantframe.sampconf import ctp_setting_simnow,ctp_setting_real

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True
SETTINGS["log.file"] = True
def process_tick_event(event: Event) -> None:
    """
    Process log event.
    """
    tick = event.data
    print('{}'.format(tick))

def process_log_event(event: Event) -> None:
    """
    Process log event.
    """
    print('{}'.format(event))
## ctpgateway的初始化只需要一个事件引擎，他的所有回调都会被解析成为事件引擎的形式
## 并将对应的数据压入事件引擎。但是缺乏处理函数，比如write_log, LogData被压入事件引擎的队列。
## 日志数据不会被日志引擎获取。

EVENT_RECORDER_LOG: str = "eRecorderLog"
event_engine = EventEngine()
main_engine = MainEngine(event_engine)  #主引擎装载事件引擎
event_engine.register(EVENT_TICK,process_tick_event)
# app引擎是单独的日志事件，无法与logengine共用。
event_engine.register(EVENT_RECORDER_LOG, process_log_event)

cg = main_engine.add_gateway(CtpGateway)     # 添加底层接口
cg.connect(ctp_setting_real)
RE = RecorderEngine(main_engine,event_engine)

# 等待获取所有合约信息
time.sleep(5)

#必须等待oms更新完所有的合约信息，才可以添加记录
RE.add_bar_recording("au2212.SHFE")
RE.add_tick_recording("au2212.SHFE")
# oms = main_engine.get_engine('oms')
# oms.contracts['ag2112.SHFE']

sreq = SubscribeRequest("au2212",Exchange.SHFE)
cg.subscribe(sreq)
sreq2 = SubscribeRequest("au2212",Exchange.SHFE)
cg.subscribe(sreq2)

#%% RE.tick_recordings/bar_recording
# 用来筛选需要记录的合约信息。
RE.tick_recordings
# {'ag2112.SHFE': {'symbol': 'ag2112',
#   'exchange': 'SHFE',
#   'gateway_name': 'CTP'}}

RE.add_tick_recording("LOCAL.ag2112")
# Event('eRecorderLog', '添加Tick记录成功：LOCAL.ag2112')
# {'ag2112.SHFE': {'symbol': 'ag2112',
#   'exchange': 'SHFE',
#   'gateway_name': 'CTP'},
#  'LOCAL.ag2112': {}}
RE.remove_tick_recording("LOCAL.ag2112")
# Event('eRecorderLog', '移除Tick记录成功：LOCAL.ag2112')

RE.add_bar_recording("LOCAL.ag2112")
# Event('eRecorderLog', '已在K线记录列表中：LOCAL.ag2112')
RE.remove_bar_recording("LOCAL.ag2112")
# Event('eRecorderLog', '移除K线记录成功：LOCAL.ag2112')


#%% ticks
# RE的ticks中为什么是空的，因为定时事件出发，已经入库了。
# 以下信息是在对应的process方法中通过打印得到的。

RE.ticks
# defaultdict(list, {})
# {
#     'ag2112.SHFE': 
#         [
#             TickData(gateway_name='CTP', symbol='ag2112', exchange=<Exchange.SHFE: 'SHFE'>, datetime=datetime.datetime(2021, 12, 11, 2, 30, 2, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>), name='白银2112', volume=1768, turnover=0, open_interest=29258.0, last_price=4592.0, last_volume=0, limit_up=5011.0, limit_down=4100.0, open_price=4539.0, high_price=4606.0, low_price=4463.0, pre_close=4519.0, bid_price_1=4565.0, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=4608.0, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=4, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=12, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0, localtime=None)
#         ]
#      'au2112.SHFE': 
#         [
#              TickData(gateway_name='CTP', symbol='au2112', exchange=<Exchange.SHFE: 'SHFE'>, datetime=datetime.datetime(2021, 12, 11, 2, 30, 2, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>), name='黄金2112', volume=9, turnover=0, open_interest=2172.0, last_price=366.0, last_volume=0, limit_up=386.06, limit_down=342.36, open_price=366.0, high_price=366.0, low_price=366.0, pre_close=364.12, bid_price_1=363.1, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=368.0, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=3, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=15, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0, localtime=None)
#         ]
# }


#%% 数据入库
