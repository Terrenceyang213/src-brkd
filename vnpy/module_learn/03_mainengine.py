#%%
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.object import LogData
from vnpy.trader.setting import SETTINGS
from logging import INFO
##############################################################
SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True
SETTINGS["log.file"] = True

event_engine = EventEngine()            #事件引擎
main_engine = MainEngine(event_engine)  #主引擎装载事件引擎
main_engine.add_gateway(CtpGateway)     # 添加底层接口
main_engine.engines
# {
# 'log': <vnpy.trader.engine.LogEngine at 0x25b984aba48>,
# 'oms': <vnpy.trader.engine.OmsEngine at 0x25ba9ba3d88>,
# 'email': <vnpy.trader.engine.EmailEngine at 0x25ba9bbf648>
# }

#%% 事件引擎
main_engine.event_engine._handlers
# defaultdict(list,
#             {'eLog': [<bound method LogEngine.process_log_event of <vnpy.trader.engine.LogEngine object at 0x0000025B984ABA48>>],
#              'eTick.': [<bound method OmsEngine.process_tick_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>],
#              'eOrder.': [<bound method OmsEngine.process_order_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>],
#              'eTrade.': [<bound method OmsEngine.process_trade_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>],
#              'ePosition.': [<bound method OmsEngine.process_position_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>],
#              'eAccount.': [<bound method OmsEngine.process_account_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>],
#              'eContract.': [<bound method OmsEngine.process_contract_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>],
#              'eQuote.': [<bound method OmsEngine.process_quote_event of <vnpy.trader.engine.OmsEngine object at 0x0000025BA9BA3D88>>]
#               }
#           )

main_engine.event_engine._queue.qsize()
# 0

#%% 日志引擎
# 日志写到哪里去？
main_engine.engines['log']
# <vnpy.trader.engine.LogEngine at 0x25b984aba48>

main_engine.engines['log'].logger
# <Logger VN Trader (CRITICAL)> 日志层级CRITICAL
# 日志位置：C:\Users\Terry\.vntrader\log\

main_engine.write_log("hahahaahha")
main_engine.event_engine._queue.qsize()
# 1
# 日志等级默认CRITICAL
# 在setting.py 中使用INFO层级则能够记录日志信息。
# 也就是说，主引擎的write_log函数只能写INFO层级的日志

log = LogData(msg="111", gateway_name="ctp")
# LogData(gateway_name='ctp', msg='111', level=20)
# 主引擎创建的LogData默认是INFO级别的（INFO=20）

# 对新的日志事件进行监听
from vnpy_ctastrategy.base import EVENT_CTA_LOG
log_engine = main_engine.get_engine("log")
event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
main_engine.write_log("注册日志事件监听")


#%% order management system/ 需要外接事件源才能测试。
main_engine.engines['']


#%% email 引擎/ no problem
# 邮箱需要在setting.py配置授权码,使用qq邮箱的登陆密码是无效的。
# 可接收，没问题
main_engine.engines['email'].send_email('test','testcontent')

