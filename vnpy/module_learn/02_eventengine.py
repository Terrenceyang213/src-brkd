#%% event使用

from vnpy.event import Event,EventEngine
import numpy as np
# 定义一个定时事件类型
EVENT_TIMER = "eTimer" #定时事件type
event = Event("eTimer",'1') # 定时事件不需要data
# <vnpy.event.engine.Event at 0x1f194ae5a08>

event
# Event('eTimer', '1')

event2 = Event(EVENT_TIMER , 1)
event2
# Event('eTimer', 1)

#%% event中的数据是以引用的形式存在的。
exdata3 = np.array([1,2,3,4])

event3 = Event("event with data", exdata3)
# Event('event with data', array([1, 2, 3, 4]))

event3.data is exdata3
# True



#%% 定义与使用一个引擎
from vnpy.event import Event,EventEngine
import numpy as np
from time import sleep

EVENT_TIMER = "eTimer"
engine = EventEngine()

# 定义一个事件，
exdata = np.array([1,2,3,4])
print("exdata defination",exdata)

data_event = Event("event with data", exdata)
time_event = Event(EVENT_TIMER, exdata)
print("event defination finished",exdata)


# 定义处理这个事件的函数
def data_event_handler(event:data_event):
    print(event)

def time_event_handler(event:time_event):
    if event.data is not None:
        event.data += 1
    print(event)

print("event processor finished", exdata)

# 注册
engine.register(data_event.type, data_event_handler)
engine.register(time_event.type, time_event_handler)
print("register finished", exdata)

for i in range(50):
    engine.put(data_event)
    engine.put(time_event)
print("event dequeue", exdata)

print("engine start", exdata)
engine.start()

engine.stop()
print("end engine",exdata)

# exdata defination [1 2 3 4]
# event defination finished [1 2 3 4]
# event processor finished [1 2 3 4]
# register finished [1 2 3 4]
# event dequeue [1 2 3 4]

# engine start [1 2 3 4]
# Event('event with data', array([1, 2, 3, 4]))
# Event('eTimer', array([2, 3, 4, 5]))
# Event('event with data', array([2, 3, 4, 5]))
# Event('eTimer', array([3, 4, 5, 6]))
# Event('event with data', array([3, 4, 5, 6]))
# Event('eTimer', array([4, 5, 6, 7]))
# Event('event with data', array([4, 5, 6, 7]))
# end engine [4 5 6 7]

# 在这次运行中，有一个dataevent没有触发其处理事件
# 有两个timeevent没有运行
# 也就是说，中断会导致事件队列丢失


# %% 如何触发所有的event
from vnpy.event import Event,EventEngine
import numpy as np
from time import sleep

# 定义事件类型
EVENT_TIMER = "eTimer"

# 定义一个事件，
exdata = np.array([1, 2, 3, 4, 5])
data_event = Event("event with data", exdata)
time_event = Event(EVENT_TIMER, exdata)

# 定义处理这个事件的函数
def data_event_handler(event:data_event):
    event.data += 10
    print(event)

def time_event_handler(event:time_event):
    if event.data is not None:
        event.data -= 1
    print(event)

engine = EventEngine()

engine.register(data_event.type, data_event_handler)
engine.register(time_event.type, time_event_handler)
print("register finished: ", exdata)

for i in range(50):
    engine.put(data_event)
    engine.put(time_event)
print("event dequeue: ", exdata)


print("engine start******************************", exdata)
engine.start()


engine.stop()
print("end engine********************************", exdata)

# register finished:  [1 2 3 4 5]
# event dequeue:  [1 2 3 4 5]
# engine start****************************** [1 2 3 4 5]
# Event('event with data', array([11, 12, 13, 14, 15]))
# Event('eTimer', array([10, 11, 12, 13, 14]))
# Event('event with data', array([20, 21, 22, 23, 24]))
# Event('eTimer', array([19, 20, 21, 22, 23]))
# Event('event with data', array([29, 30, 31, 32, 33]))
# Event('eTimer', array([28, 29, 30, 31, 32]))
# Event('event with data', array([38, 39, 40, 41, 42]))
# Event('eTimer', array([37, 38, 39, 40, 41]))
# Event('event with data', array([47, 48, 49, 50, 51]))
# Event('eTimer', array([46, 47, 48, 49, 50]))
# Event('event with data', array([56, 57, 58, 59, 60]))
# Event('eTimer', array([55, 56, 57, 58, 59]))
# Event('event with data', array([65, 66, 67, 68, 69]))
# Event('eTimer', array([64, 65, 66, 67, 68]))
# Event('event with data', array([74, 75, 76, 77, 78]))
# Event('eTimer', array([73, 74, 75, 76, 77]))
# Event('event with data', array([83, 84, 85, 86, 87]))
# Event('eTimer', array([82, 83, 84, 85, 86]))
# Event('event with data', array([92, 93, 94, 95, 96]))
# Event('eTimer', array([91, 92, 93, 94, 95]))
# Event('event with data', array([101, 102, 103, 104, 105]))
# Event('eTimer', array([100, 101, 102, 103, 104]))
# show more (open the raw output data in a text editor) ...
# ......
# Event('event with data', array([110, 111, 112, 113, 114]))
# Event('eTimer', array([109, 110, 111, 112, 113]))
# Event('event with data', array([119, 120, 121, 122, 123]))
# Event('eTimer', array([118, 119, 120, 121, 122]))
# end engine******************************** [118 119 120 121 122]

# 同样的情况，停止必然导致event丢失

#%% 如果让引擎主进程睡眠一段时间
print("engine start******************************", exdata)
engine.start()
sleep(20)
engine.stop()
print("end engine********************************", exdata)
# threads can only be started once
# engine should be defined again


#%% engine sleep 2s
from vnpy.event import Event,EventEngine
import numpy as np
from time import sleep

# 定义事件类型
EVENT_TIMER = "eTimer"

# 定义一个事件，
exdata = np.array([1, 2, 3, 4, 5])
data_event = Event("event with data", exdata)
time_event = Event(EVENT_TIMER, exdata)

# 定义处理这个事件的函数
def data_event_handler(event:data_event):
    event.data += 10
    print(event)

def time_event_handler(event:time_event):
    if event.data is not None:
        event.data -= 1
    print(event)

engine = EventEngine()

engine.register(data_event.type, data_event_handler)
engine.register(time_event.type, time_event_handler)
print("register finished: ", exdata)

for i in range(50):
    engine.put(data_event)
    engine.put(time_event)
print("event dequeue: ", exdata)


print("engine start******************************", exdata)
engine.start()
sleep(2)
engine.stop()
print("end engine********************************", exdata)

# register finished:  [1 2 3 4 5]
# event dequeue:  [1 2 3 4 5]
# engine start****************************** [1 2 3 4 5]
# Event('event with data', array([11, 12, 13, 14, 15]))
# Event('eTimer', array([10, 11, 12, 13, 14]))
# Event('event with data', array([20, 21, 22, 23, 24]))
# Event('eTimer', array([19, 20, 21, 22, 23]))
# Event('event with data', array([29, 30, 31, 32, 33]))
# Event('eTimer', array([28, 29, 30, 31, 32]))
# Event('event with data', array([38, 39, 40, 41, 42]))
# Event('eTimer', array([37, 38, 39, 40, 41]))
# Event('event with data', array([47, 48, 49, 50, 51]))
# Event('eTimer', array([46, 47, 48, 49, 50]))
# Event('event with data', array([56, 57, 58, 59, 60]))
# Event('eTimer', array([55, 56, 57, 58, 59]))
# Event('event with data', array([65, 66, 67, 68, 69]))
# Event('eTimer', array([64, 65, 66, 67, 68]))
# Event('event with data', array([74, 75, 76, 77, 78]))
# Event('eTimer', array([73, 74, 75, 76, 77]))
# Event('event with data', array([83, 84, 85, 86, 87]))
# Event('eTimer', array([82, 83, 84, 85, 86]))
# Event('event with data', array([92, 93, 94, 95, 96]))
# Event('eTimer', array([91, 92, 93, 94, 95]))
# Event('event with data', array([101, 102, 103, 104, 105]))
# Event('eTimer', array([100, 101, 102, 103, 104]))

# show more (open the raw output data in a text editor) ...

# Event('eTimer', array([442, 443, 444, 445, 446]))
# Event('event with data', array([452, 453, 454, 455, 456]))
# Event('eTimer', array([451, 452, 453, 454, 455]))
# Event('eTimer', None)
# end engine******************************** [451 452 453 454 455]


#%% engine.stop调用后，生产者进程还可以继续往队列里面放事件
# 但是这个engine已经不能再调起了。

from vnpy.event import Event,EventEngine
import numpy as np
from time import sleep
from threading import Thread

# 定义事件类型
EVENT_TIMER = "eTimer"

# 定义一个事件，
exdata = np.array([1, 2, 3, 4, 5])
data_event = Event("event with data", exdata)
time_event = Event(EVENT_TIMER, exdata)

# 定义处理这个事件的函数
def data_event_handler(event:data_event):
    event.data += 10
    print(event)

def time_event_handler(event:time_event):
    if event.data is not None:
        event.data -= 1
    print(event)

engine = EventEngine()

engine.register(data_event.type, data_event_handler)
engine.register(time_event.type, time_event_handler)
print("register finished: ", exdata)

for i in range(50):
    engine.put(data_event)
    engine.put(time_event)
print("event dequeue: ", exdata)


print("engine start******************************", exdata)
engine.start()
sleep(2)
engine.stop()
print("end engine********************************", exdata)

engine.put(data_event)
print(engine._queue)
# <queue.Queue object at 0x000001669EF51848>

# engine.start()
# RuntimeError: threads can only be started once