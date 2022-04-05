#%% 
from vnpy import event
from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.object import LogData,SubscribeRequest, TickData
from vnpy.trader.event import EVENT_LOG, EVENT_TICK
from vnpy.trader.constant import Exchange
from vnpy.trader.setting import SETTINGS
from logging import INFO
from datetime import datetime, time
from time import sleep
from quantframe.sampconf import ctp_setting_simnow,ctp_setting_real

# 配置信息
SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True
SETTINGS["log.file"] = True




#%% 测试目的，在主引擎中使用gateway，实现相关功能。


#%% 正常登陆
## 问题1：一直无回应:因为端口错误，onFrontConnect回调未必触发。
from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.setting import SETTINGS
from logging import INFO
from quantframe.sampconf import ctp_setting_simnow,ctp_setting_real

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True
SETTINGS["log.file"] = True
## ctpgateway的初始化只需要一个事件引擎，他的所有回调都会被解析成为事件引擎的形式
## 并将对应的数据压入事件引擎。但是缺乏处理函数，比如write_log, LogData被压入事件引擎的队列。
## 日志数据不会被日志引擎获取。


event_engine = EventEngine()
main_engine = MainEngine(event_engine)  #主引擎装载事件引擎
cg = main_engine.add_gateway(CtpGateway)     # 添加底层接口
cg.connect(ctp_setting_simnow)



#%% 模块:登陆
from vnpy.event import EventEngine, Event
from vnpy.trader.event import EVENT_LOG
from vnpy.gateway.ctp import CtpGateway
from quantframe.sampconf import ctp_setting_simnow,ctp_setting_real

#1 处理log事件的函数
def process_log_event(event: Event) -> None:
    """
    Process log event.
    """
    log = event.data
    print('{}:{}'.format(log.level, log.msg))

#2 事件引擎，注册函数，并启动引擎
event_engine = EventEngine()
event_engine.register(EVENT_LOG,process_log_event)
event_engine.start()


#3 初始化CTPgateway
cg = CtpGateway(event_engine, "CTP")
cg.connect(ctp_setting_simnow)


#4 登陆但无日志显示，多半是登陆req没有成功，回调函数未被启动。
# 20:行情服务器连接成功
# 20:交易服务器连接成功
# 20:行情服务器登录成功
# 20:交易服务器授权验证成功
# 20:交易服务器登录成功
# 20:结算信息确认成功
# 20:合约信息查询成功


#%% 极简模块:订阅行情-收取行情
from vnpy.event import EventEngine, Event
from vnpy.trader.event import EVENT_TICK,EVENT_LOG
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange
import time
from quantframe.sampconf import ctp_setting_simnow,ctp_setting_real


#1 处理Tick事件的函数
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
    log = event.data
    print('{}:{}'.format(log.level, log.msg))

#2 事件引擎，注册函数，并启动引擎，初始化Gateway
event_engine = EventEngine()
event_engine.register(EVENT_TICK,process_tick_event)
event_engine.register(EVENT_LOG,process_log_event)
event_engine.start()
cg = CtpGateway(event_engine, "CTP")
cg.connect(ctp_setting_real) #登陆信息

time.sleep(5)
sreq = SubscribeRequest("ag2212",Exchange.SHFE) #留意这个编号，随着时间的推移，编号会不断改变
cg.subscribe(sreq)

# TickData(gateway_name='CTP', symbol='ag2112', exchange=<Exchange.SHFE: 'SHFE'>
# , datetime=datetime.datetime(2021, 12, 10, 2, 30, 2, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
# , name='白银2112', volume=4486, turnover=0, open_interest=39462.0, last_price=4572.0, last_volume=0
# , limit_up=5093.0, limit_down=4167.0, open_price=4592.0, high_price=4598.0, low_price=4535.0, pre_close=4604.0
# , bid_price_1=4562.0, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0
# , ask_price_1=4580.0, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0
# , bid_volume_1=2, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0
# , ask_volume_1=4, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0, localtime=None)
# TickData会不断的传送过来

#%% 