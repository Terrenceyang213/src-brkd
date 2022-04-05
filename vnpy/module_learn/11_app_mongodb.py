#%%
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database
from pymongo.cursor import Cursor
from pymongo.collection import Collection
from pymongo.results import DeleteResult
from tzlocal import get_localzone
from pytz import timezone

#%% 登陆信息
database: str = "mongodb" #mongo里面的库名
host: str = "localhost"
port: int = 27017
username: str = ""
password: str = ""

client = MongoClient(
    host=host,
    port=port,
    tz_aware=True,
    tzinfo=timezone(get_localzone().zone)
)
# MongoClient(host=['localhost:27017'], document_class=dict
#           , tz_aware=True, connect=True
#           , tzinfo=<DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>)

db: Database = client[database]
# Database(MongoClient(host=['localhost:27017'], document_class=dict
#           , tz_aware=True, connect=True
#           , tzinfo=<DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>)
#           , 'mongodb')

bar_collection: Collection = db["bar_data"]
# Collection(Database(MongoClient(host=['localhost:27017']
#           , document_class=dict, tz_aware=True , connect=True
#           , tzinfo=<DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>)
#           , 'mongodb'), 'bar_data')

# %% 创建index
bar_collection.create_index(
            [
                ("exchange", ASCENDING),
                ("symbol", ASCENDING),
                ("interval", ASCENDING),
                ("datetime", ASCENDING),
            ],
            unique=True
        )
# 'exchange_1_symbol_1_interval_1_datetime_1'

# %% upsert数据
# 如果存在数据则更新，如果没有则插入
# 样本数据：{ "_id" : ObjectId("61c43affe538165a6280c995"), "user" : "test" }

user_collection = db["user"]
filter = {"user":"test"} #一般用index
d = {"user":"testtesttest"}
user_collection.replace_one({"user":"test"}, {"user":"testtesttest"}, upsert=True)
# { "_id" : ObjectId("61c43affe538165a6280c995"), "user" : "testtesttest" }

user_collection.replace_one({"user":"55555"}, {"user":"55555","passwd":"abc"}, upsert=True)
# { "_id" : ObjectId("61c43affe538165a6280c995"), "user" : "testtesttest" }
# { "_id" : ObjectId("61c43b57701f2115178d59cb"), "user" : "55555", "passwd" : "abc" }

# %% 读取数据find
filter = {"user": "testtesttest"}
c = user_collection.find(filter)
# <pymongo.cursor.Cursor at 0x1ca935f8dc8>

# c是可迭代对象
c[0] 
# dict{'_id': ObjectId('61c43affe538165a6280c995'), 'user': 'testtesttest'}

c = user_collection.find({})
for i in c:
    print(i)
# {'_id': ObjectId('61c442e5701f2115178d5b6d'), 'user': 'testtesttest'}
# {'_id': ObjectId('61c442e5701f2115178d5b6f'), 'user': '55555', 'passwd': 'abc'}

# %% 删除数据delete_many
#

user_collection.delete_many({"user":"testtesttest"})
# { "_id" : ObjectId("61c442e5701f2115178d5b6f"), "user" : "55555", "passwd" : "abc" }


