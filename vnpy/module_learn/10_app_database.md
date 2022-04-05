# BaseDatabase
基类，规定六个接口函数
1. save_bar_data(self, bars: List[BarData]) -> bool:
2. save_tick_data(self, ticks: List[TickData]) -> bool:
3. load_bar_data(self, symbol: str, exchange: Exchange, interval: Interval, start: datetime, end: datetime) -> List[BarData]
4. load_tick_data(self, symbol: str, exchange: Exchange, start: datetime, end: datetime) -> List[TickData]
5. delete_bar_data(self, symbol: str, exchange: Exchange, interval: Interval ) -> int
6. delete_tick_data(self, symbol: str, exchange: Exchange ) -> int:
7. get_bar_overview(self) -> List[BarOverview]:

## 获取数据库的步骤
``` py
def get_database() -> BaseDatabase:
    """"""
    # Return database object if already inited
    global database
    if database:
        return database

    # Read database related global setting
    database_name: str = SETTINGS["database.name"]
    module_name: str = f"vnpy_{database_name}"

    # Try to import database module
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        print(f"找不到数据库驱动{module_name}，使用默认的SQLite数据库")
        module = import_module("vnpy_sqlite")

    # Create database object from module
    database = module.Database()
    return database
```
1. SETTINGS["database.name"]保存的是模块名vnpy_mongodb
2. module = import_module(module_name) 以此导入并获取module对象
3. module.Database() ：模块文件中是 from .mongodb_database import MongodbDatabase as Database
4. 因此配置了SETTINGS之后，获取到的是MongodbDatabase对象。

# MongodbDatabase

