# c++版功能分析（6.3.15_demo_program)
## 文件结构
在交易所提供的头文件中，分行情类和交易类两种。
- 行情类
  - request请求类：CThostFtdcMdApi
  - response回复处理类：CThostFtdcMdSpi
- 交易类
  - request请求类：CThostFtdcTraderApi
  - response回复处理类：CThostFtdcTraderSpi
- 作者继承
  - CTraderApi:CThostFtdcTraderApi,虽然继承接口Api，但是类中还有一个该父类接口的指针，CThostFtdcTraderApi *m_pApi，并且调用都通过该指针进行。主要实现就是先打印信息，然后通过父类指针对用Req请求
  - CTraderSpi:CThostFtdcTraderSpi,主要实现事件响应时打印信息
- 作者设计
  - CSimpleHandler：用以生成数据结构发送Req，获取数据打印错误信息
    - 继承自CTraderSpi
    - 包含一个CTraderApi指针
    - 将Req/Rsp整合至一一个类中。
  - CSimpleMdHandler:与上面类似
    - 继承自CThostFtdcMdSpi（因为市场行业没有MdSpi）
    - 包含一个CThostFtdcMdApi指针
    - 整合Spi和Api

### ctpgateway中的实现

TdApi/MdApi封装：(C++,pybind11)
- On回调继承Spi接口（注意大写On）
  - 直接从服务器获取回调信息
  - 将信息结构体拆包，再打包成统一的task结构，放入TaskQueue
- Process内部线程逐个出列，然后按照taskname来调用对应的Process函数
  - process函数对task.data解包，然后放入一个字典结构dict中
  - 将dict传入一个虚函数on回调
- on回调是开放给python实现的接口。（注意小写on）

CtpTdApi/CtpMdApi封装：（python）
- 继承TdApi/MdApi
- 实现on（小写）回调方法，作为真正的回调处理部分。
- 
## 配置

### 证券
 
``` conf
FrontAddr=
FrontMdAddr=
BrokerID=
UserID=
Password=
InvestorID=
UserProductInfo=
AuthCode=
AppID=
```
- 交易端口：
- 行情端口：
  

该配置信息已经在程序中得到验证，可以成功获取转账流水。

### Simnow
``` conf
FrontAddr=
FrontMdAddr=
BrokerID=
UserID=
Password=
InvestorID=
UserProductInfo=
AuthCode=
AppID=
```

### 变量命名

``` c++
CSimpleHandler sh(pUserApi); //交易类Api/Spi整合类
```

## 用户登陆

1. 操作步骤：
   1. 102（客户端认证）
   2. 101（用户登陆请求）
   
### 102客户端认证

``` c++
case 102:
{
	sh.ReqAuthenticate();
	_getch();
	break;
}
```
``` c++
void ReqAuthenticate()
{
	//客户端验证需要五个字段
	//Req相关功能必须要靠Api实现
	//strcpy_s(g_chUserProductInfo, getConfig("config","UserProductInfo").c_str());
	strcpy_s(g_chAuthCode, getConfig("config", "AuthCode")c_str());
	strcpy_s(g_chAppID, getConfig("config", "AppID").c_str();
	CThostFtdcReqAuthenticateField a = { 0 };
	strcpy_s(a.BrokerID, g_chBrokerID);
	strcpy_s(a.UserID, g_chUserID);
	//strcpy_s(a.UserProductInfo, "");
	strcpy_s(a.AuthCode, g_chAuthCode);
	strcpy_s(a.AppID, g_chAppID);
	int b = m_pUserApi->ReqAuthenticate(&a, 1);
	printf("\t客户端认证 = [%d]\n", b);
}
```
``` c++
int CTraderApi::ReqAuthenticate(CThostFtdcReqAuthenticateField *pReqAuthenticateField, int nRequestID)
{
	LOG("<ReqAuthenticate>\n");
	if (pReqAuthenticateField)
	{
		LOG("\tBrokerID [%s]\n",pReqAuthenticateField->BrokerID);
		LOG("\tUserID [%s]\n",pReqAuthenticateField->UserID);
		LOG("\tUserProductInfo [%s]\n",pReqAuthenticateField->UserProductInfo);
		LOG("\tAuthCode [%s]\n",pReqAuthenticateField->AuthCode);
		LOG("\tAppID [%s]\n",pReqAuthenticateField->AppID);
	}
	LOG("\tnRequestID [%d]\n",nRequestID);
	LOG("</ReqAuthenticate>\n");

	return m_pApi->ReqAuthenticate(pReqAuthenticateField, nRequestID);
};
```

``` c++
virtual void OnRspAuthenticate(
	CThostFtdcRspAuthenticateField *pRspAuthenticateField, CThostFtdcRspInfoField *pRspInfo,
		int nRequestID, bool bIsLast)
{
	CTraderSpi::OnRspAuthenticate(pRspAuthenticateField,pRspInfo, nRequestID, bIsLast); //父类的响应函数
	SetEvent(g_hEvent);
}
```

``` c++
void CTraderSpi::OnRspAuthenticate(
	CThostFtdcRspAuthenticateField *pRspAuthenticateField, CThostFtdcRspInfoField *pRspInfo, 
	int nRequestID, bool bIsLast) 
{
	LOG("<OnRspAuthenticate>\n");
	if (pRspAuthenticateField)
	{
		LOG("\tBrokerID [%s]\n",pRspAuthenticateField->BrokerID);
		LOG("\tUserID [%s]\n",pRspAuthenticateField->UserID);
		LOG("\tUserProductInfo [%s]\n",pRspAuthenticateField->UserProductInfo);
		LOG("\tAppID [%s]\n",pRspAuthenticateField->AppID);
		LOG("\tAppType [%c]\n",pRspAuthenticateField->AppType);
	}
	if (pRspInfo)
	{
		LOG("\tErrorMsg [%s]\n",pRspInfo->ErrorMsg);
		LOG("\tErrorID [%d]\n",pRspInfo->ErrorID);
	}
	LOG("\tnRequestID [%d]\n",nRequestID);
	LOG("\tbIsLast [%d]\n",bIsLast);
	LOG("</OnRspAuthenticate>\n");
};
```

### 101 用户登录请求
``` c++
case 101:
{
	sh.ReqUserLogin();
	_getch();
	break;
}
```

``` c++
//用户登陆请求Request
struct CThostFtdcReqUserLoginField
{
	///交易日
	TThostFtdcDateType	TradingDay;
	///经纪公司代码*
	TThostFtdcBrokerIDType	BrokerID;
	///用户代码*
	TThostFtdcUserIDType	UserID;
	///密码*
	TThostFtdcPasswordType	Password;
	///用户端产品信息
	TThostFtdcProductInfoType	UserProductInfo;
	///接口端产品信息
	TThostFtdcProductInfoType	InterfaceProductInfo;
	///协议信息
	TThostFtdcProtocolInfoType	ProtocolInfo;
	///Mac地址
	TThostFtdcMacAddressType	MacAddress;
	///动态密码
	TThostFtdcPasswordType	OneTimePassword;
	///终端IP地址
	TThostFtdcIPAddressType	ClientIPAddress;
	///登录备注
	TThostFtdcLoginRemarkType	LoginRemark;
	///终端IP端口
	TThostFtdcIPPortType	ClientIPPort;
};

void ReqUserLogin()
{   //登陆为什么只要这三个信息
	CThostFtdcReqUserLoginField reqUserLogin = { 0 };
	strcpy_s(reqUserLogin.BrokerID, g_chBrokerID);
	strcpy_s(reqUserLogin.UserID, g_chUserID);
	strcpy_s(reqUserLogin.Password, g_chPassword);
	//strcpy_s(reqUserLogin.ClientIPAddress, "::c0a8:0101");
	//strcpy_s(reqUserLogin.UserProductInfo, "123");
	// 发出登陆请求
	m_pUserApi->ReqUserLogin(&reqUserLogin, nRequestID++);
}

int CTraderApi::ReqUserLogin(
    CThostFtdcReqUserLoginField *pReqUserLoginField
    , int nRequestID)
{
	LOG("<ReqUserLogin>\n");
	if (pReqUserLoginField)
	{
		LOG("\tTradingDay [%s]\n",pReqUserLoginField->TradingDay);
		LOG("\tBrokerID [%s]\n",pReqUserLoginField->BrokerID);
		LOG("\tUserID [%s]\n",pReqUserLoginField->UserID);
		LOG("\tPassword [%s]\n",pReqUserLoginField->Password);
		LOG("\tUserProductInfo [%s]\n",pReqUserLoginField->UserProductInfo);
		LOG("\tInterfaceProductInfo [%s]\n",pReqUserLoginField->InterfaceProductInfo);
		LOG("\tProtocolInfo [%s]\n",pReqUserLoginField->ProtocolInfo);
		LOG("\tMacAddress [%s]\n",pReqUserLoginField->MacAddress);
		LOG("\tOneTimePassword [%s]\n",pReqUserLoginField->OneTimePassword);
		LOG("\tClientIPAddress [%s]\n",pReqUserLoginField->ClientIPAddress);
		LOG("\tLoginRemark [%s]\n",pReqUserLoginField->LoginRemark);
		LOG("\tClientIPPort [%d]\n",pReqUserLoginField->ClientIPPort);
	}
	LOG("\tnRequestID [%d]\n",nRequestID);
	LOG("</ReqUserLogin>\n");

	return m_pApi->ReqUserLogin(pReqUserLoginField, nRequestID);
    //CThostFtdcTraderApi *m_pApi; //这个是交易所提供的交易类
};

```

``` c++
///用户登录Response
struct CThostFtdcRspUserLoginField
{
	///交易日
	TThostFtdcDateType	TradingDay;
	///登录成功时间
	TThostFtdcTimeType	LoginTime;
	///经纪公司代码
	TThostFtdcBrokerIDType	BrokerID;
	///用户代码
	TThostFtdcUserIDType	UserID;
	///交易系统名称
	TThostFtdcSystemNameType	SystemName;
	///前置编号
	TThostFtdcFrontIDType	FrontID;
	///会话编号
	TThostFtdcSessionIDType	SessionID;
	///最大报单引用
	TThostFtdcOrderRefType	MaxOrderRef;
	///上期所时间
	TThostFtdcTimeType	SHFETime;
	///大商所时间
	TThostFtdcTimeType	DCETime;
	///郑商所时间
	TThostFtdcTimeType	CZCETime;
	///中金所时间
	TThostFtdcTimeType	FFEXTime;
	///能源中心时间
	TThostFtdcTimeType	INETime;
};

virtual void CSimpleHandler::OnRspUserLogin(
        CThostFtdcRspUserLoginField *pRspUserLogin //Rsp
        , CThostFtdcRspInfoField *pRspInfo
        , int nRequestID
        , bool bIsLast)
{
	FrontID = pRspUserLogin->FrontID;
	SessionID = pRspUserLogin->SessionID;
	CTraderSpi::OnRspUserLogin(pRspUserLogin, pRspInfo, nRequestID, IsLast);
	if (pRspInfo->ErrorID != 0)
	//if (pRspInfo)
	{
		LOG("\tFailed to login, errorcode=[%d]\n \terrormsg=[%s]\n trequestid = [%d]\n \tchain = [%d]\n",
			pRspInfo->ErrorID, pRspInfo->ErrorMsg, nRequestID, bIsLast);
		//exit(-1);
	}
	SetEvent(g_hEvent);
}

```
## 行情查询 100
``` c++
case 110:
{
	string g_chFrontMdaddr = getConfig("config""FrontMdAddr");
	cout << "g_chFrontMdaddr = " << g_chFrontMdaddr <"\n" << endl;
	CThostFtdcMdApi  *pUserMdApi = 
		CThostFtdcMdApi::CreateFtdcMdApi(".\\flow\\md");
	CSimpleMdHandler ash(pUserMdApi);

	pUserMdApi->RegisterSpi(&ash);
	pUserMdApi->RegisterFront(const_cast<char (g_chFrontMdaddr.c_str()));
	pUserMdApi->Init();
	WaitForSingleObject(xinhao, INFINITE);
	sh.ReqQryInstrument();//注意，使用的是交易类Api查询合约
	WaitForSingleObject(xinhao, INFINITE);
	ash.SubscribeMarketData();//订阅行情
	_getch();
	pUserMdApi->Release();
	break;
}
```

### 查询合约

``` c++
void ReqQryInstrument()
{
	CThostFtdcQryInstrumentField a = { 0 };
	strcpy_s(a.ExchangeID, g_chExchangeID);
	strcpy_s(a.InstrumentID, g_chInstrumentID);
	//strcpy_s(a.ExchangeInstID,"");
	//strcpy_s(a.ProductID, "m");
	int b = m_pUserApi->ReqQryInstrument(&a, nRequestID++);
	LOG((b == 0) ? "请求查询合约......发送成功\n" : "请求查询合约......发送失败，错误序号=[%d]\n", b);
}
```

``` c++
int CTraderApi::ReqQryInstrument(CThostFtdcQryInstrumentField *pQryInstrument, int nRequestID)
{
	LOG("<ReqQryInstrument>\n");
	if (pQryInstrument)
	{
		LOG("\tInstrumentID [%s]\n",pQryInstrument->InstrumentID);
		LOG("\tExchangeID [%s]\n",pQryInstrument->ExchangeID);
		LOG("\tExchangeInstID [%s]\n",pQryInstrument->ExchangeInstID);
		LOG("\tProductID [%s]\n",pQryInstrument->ProductID);
	}
	LOG("\tnRequestID [%d]\n",nRequestID);
	LOG("</ReqQryInstrument>\n");

	return m_pApi->ReqQryInstrument(pQryInstrument, nRequestID);
};
```
回调函数究竟是父类的被执行，还是子类的被执行？
``` c++
子类
virtual void OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast)
{
	LOG("<OnRspQryInstrument>\n");
	if (pInstrument)
	{
		md_InstrumentID.push_back(pInstrument->InstrumentID);
		LOG("\tInstrumentID [%s]\n", pInstrument->InstrumentID);
		LOG("\tExchangeID [%s]\n", pInstrument->ExchangeID);
		LOG("\tInstrumentName [%s]\n", pInstrument->InstrumentName);
		LOG("\tExchangeInstID [%s]\n", pInstrument->ExchangeInstID);
		LOG("\tProductID [%s]\n", pInstrument->ProductID);
		LOG("\tCreateDate [%s]\n", pInstrument->CreateDate);
		/*LOG("\tOpenDate [%s]\n", pInstrument->OpenDate);
		LOG("\tExpireDate [%s]\n", pInstrument->ExpireDate);
		LOG("\tStartDelivDate [%s]\n", pInstrument->StartDelivDate);
		LOG("\tEndDelivDate [%s]\n", pInstrument->EndDelivDate);
		LOG("\tUnderlyingInstrID [%s]\n", pInstrument->UnderlyingInstrID);
		LOG("\tDeliveryYear [%d]\n", pInstrument->DeliveryYear);
		LOG("\tDeliveryMonth [%d]\n", pInstrument->DeliveryMonth);
		LOG("\tMaxMarketOrderVolume [%d]\n", pInstrument->MaxMarketOrderVolume);
		LOG("\tMinMarketOrderVolume [%d]\n", pInstrument->MinMarketOrderVolume);
		LOG("\tMaxLimitOrderVolume [%d]\n", pInstrument->MaxLimitOrderVolume);
		LOG("\tMinLimitOrderVolume [%d]\n", pInstrument->MinLimitOrderVolume);
		LOG("\tVolumeMultiple [%d]\n", pInstrument->VolumeMultiple);
		LOG("\tIsTrading [%d]\n", pInstrument->IsTrading);
		LOG("\tProductClass [%c]\n", pInstrument->ProductClass);
		LOG("\tInstLifePhase [%c]\n", pInstrument->InstLifePhase);
		LOG("\tPositionType [%c]\n", pInstrument->PositionType);
		LOG("\tPositionDateType [%c]\n", pInstrument->PositionDateType);
		LOG("\tMaxMarginSideAlgorithm [%c]\n", pInstrument->MaxMarginSideAlgorithm);
		LOG("\tOptionsType [%c]\n", pInstrument->OptionsType);
		LOG("\tCombinationType [%c]\n", pInstrument->CombinationType);
		LOG("\tPriceTick [%.8lf]\n", pInstrument->PriceTick);
		LOG("\tLongMarginRatio [%.8lf]\n", pInstrument->LongMarginRatio);
		LOG("\tShortMarginRatio [%.8lf]\n", pInstrument->ShortMarginRatio);
		LOG("\tStrikePrice [%.8lf]\n", pInstrument->StrikePrice);
		LOG("\tUnderlyingMultiple [%.8lf]\n", pInstrument->UnderlyingMultiple);*/
	}
	if (pRspInfo)
	{
		LOG("\tErrorMsg [%s]\n", pRspInfo->ErrorMsg);
		LOG("\tErrorID [%d]\n", pRspInfo->ErrorID);
	}
	LOG("\tnRequestID [%d]\n", nRequestID);
	LOG("\tbIsLast [%d]\n", bIsLast);
	LOG("</OnRspQryInstrument>\n");
	if (bIsLast)
	{
		SetEvent(xinhao);
	}
}
```

``` c++ 
父类
void CTraderSpi::OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) 
{
	LOG("<OnRspQryInstrument>\n");
	if (pInstrument)
	{
		LOG("\tInstrumentID [%s]\n",pInstrument->InstrumentID);
		LOG("\tExchangeID [%s]\n",pInstrument->ExchangeID);
		LOG("\tInstrumentName [%s]\n",pInstrument->InstrumentName);
		LOG("\tExchangeInstID [%s]\n",pInstrument->ExchangeInstID);
		LOG("\tProductID [%s]\n",pInstrument->ProductID);
		LOG("\tCreateDate [%s]\n",pInstrument->CreateDate);
		LOG("\tOpenDate [%s]\n",pInstrument->OpenDate);
		LOG("\tExpireDate [%s]\n",pInstrument->ExpireDate);
		LOG("\tStartDelivDate [%s]\n",pInstrument->StartDelivDate);
		LOG("\tEndDelivDate [%s]\n",pInstrument->EndDelivDate);
		LOG("\tUnderlyingInstrID [%s]\n",pInstrument->UnderlyingInstrID);
		LOG("\tDeliveryYear [%d]\n",pInstrument->DeliveryYear);
		LOG("\tDeliveryMonth [%d]\n",pInstrument->DeliveryMonth);
		LOG("\tMaxMarketOrderVolume [%d]\n",pInstrument->MaxMarketOrderVolume);
		LOG("\tMinMarketOrderVolume [%d]\n",pInstrument->MinMarketOrderVolume);
		LOG("\tMaxLimitOrderVolume [%d]\n",pInstrument->MaxLimitOrderVolume);
		LOG("\tMinLimitOrderVolume [%d]\n",pInstrument->MinLimitOrderVolume);
		LOG("\tVolumeMultiple [%d]\n",pInstrument->VolumeMultiple);
		LOG("\tIsTrading [%d]\n",pInstrument->IsTrading);
		LOG("\tProductClass [%c]\n",pInstrument->ProductClass);
		LOG("\tInstLifePhase [%c]\n",pInstrument->InstLifePhase);
		LOG("\tPositionType [%c]\n",pInstrument->PositionType);
		LOG("\tPositionDateType [%c]\n",pInstrument->PositionDateType);
		LOG("\tMaxMarginSideAlgorithm [%c]\n",pInstrument->MaxMarginSideAlgorithm);
		LOG("\tOptionsType [%c]\n",pInstrument->OptionsType);
		LOG("\tCombinationType [%c]\n",pInstrument->CombinationType);
		LOG("\tPriceTick [%.8lf]\n",pInstrument->PriceTick);
		LOG("\tLongMarginRatio [%.8lf]\n",pInstrument->LongMarginRatio);
		LOG("\tShortMarginRatio [%.8lf]\n",pInstrument->ShortMarginRatio);
		LOG("\tStrikePrice [%.8lf]\n",pInstrument->StrikePrice);
		LOG("\tUnderlyingMultiple [%.8lf]\n",pInstrument->UnderlyingMultiple);
	}
	if (pRspInfo)
	{
		LOG("\tErrorMsg [%s]\n",pRspInfo->ErrorMsg);
		LOG("\tErrorID [%d]\n",pRspInfo->ErrorID);
	}
	LOG("\tnRequestID [%d]\n",nRequestID);
	LOG("\tbIsLast [%d]\n",bIsLast);
	LOG("</OnRspQryInstrument>\n");
};
```
### 订阅行情
``` c++
void SubscribeMarketData()//收行情
{
	int md_num = 0;
	char **ppInstrumentID = new char*[5000];
	for (int count1 = 0; count1 <= md_InstrumentID.size() / 500; count1++)
	{
		if (count1 < md_InstrumentID.size() / 500)
		{
			int a = 0;
			for (a; a < 500; a++)
			{
				ppInstrumentID[a] = const_cast<char *>(md_InstrumentID.at(md_num).c_str());
				md_num++;
			}
			int result = m_pUserMdApi->SubscribeMarketData(ppInstrumentID, a);
			LOG((result == 0) ? "订阅行情请求1......发送成功\n" : "订阅行情请求1......发送失败，错误序号=[%d]\n", result);
		}
		else if (count1 = md_InstrumentID.size() / 500)
		{
			int count2 = 0;
			for (count2; count2 < md_InstrumentID.size() % 500; count2++)
			{
				ppInstrumentID[count2] = const_cast<char *>(md_InstrumentID.at(md_num).c_str());
				md_num++;
			}
			int result = m_pUserMdApi->SubscribeMarketData(ppInstrumentID, count2);
			LOG((result == 0) ? "订阅行情请求2......发送成功\n" : "订阅行情请求2......发送失败，错误序号=[%d]\n", result);
		}
	}
}

```



# 2.Ctp Gateway

## 2.1 登陆

### 2.1.1 极简模块：登陆

``` python
from vnpy.event import EventEngine, Event
from vnpy.trader.event import EVENT_LOG
from vnpy.gateway.ctp import CtpGateway
ctp_setting_simnow = {
#......
}
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

# 20:行情服务器连接成功
# 20:交易服务器连接成功
# 20:行情服务器登录成功
# 20:交易服务器授权验证成功
# 20:交易服务器登录成功
# 20:结算信息确认成功
# 20:合约信息查询成功
```

## 2.2 行情查询

### 2.2.1 行情查询运行逻辑
``` python
@dataclass
class SubscribeRequest:
    """
    Request sending to specific gateway for subscribing tick data update.
    """

    symbol: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
```

``` python
# CtpMdApi()
    def subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        if self.login_status:
            self.subscribeMarketData(req.symbol)
        self.subscribed.add(req.symbol)
```

``` python
#class CtpMdApi(MdApi):
    def onRtnDepthMarketData(self, data: dict) -> None:
        """行情数据推送"""
        # 过滤没有时间戳的异常行情数据
        if not data["UpdateTime"]:
            return

        # 过滤还没有收到合约数据前的行情推送
        symbol: str = data["InstrumentID"]
        contract: ContractData = symbol_contract_map.get(symbol, None)
        if not contract:
            return

        # 对大商所的交易日字段取本地日期
        if contract.exchange == Exchange.DCE:
            date_str: str = self.current_date
        else:
            date_str: str = data["ActionDay"]

        timestamp: str = f"{date_str} {data['UpdateTime']}.{int(data['UpdateMillisec']/100)}"
        dt: datetime = datetime.strptime(timestamp, "%Y%m%d %H:%M:%S.%f")
        dt = CHINA_TZ.localize(dt)

        tick: TickData = TickData(
            symbol=symbol,
            exchange=contract.exchange,
            datetime=dt,
            name=contract.name,
            volume=data["Volume"],
            open_interest=data["OpenInterest"],
            last_price=adjust_price(data["LastPrice"]),
            limit_up=data["UpperLimitPrice"],
            limit_down=data["LowerLimitPrice"],
            open_price=adjust_price(data["OpenPrice"]),
            high_price=adjust_price(data["HighestPrice"]),
            low_price=adjust_price(data["LowestPrice"]),
            pre_close=adjust_price(data["PreClosePrice"]),
            bid_price_1=adjust_price(data["BidPrice1"]),
            ask_price_1=adjust_price(data["AskPrice1"]),
            bid_volume_1=data["BidVolume1"],
            ask_volume_1=data["AskVolume1"],
            gateway_name=self.gateway_name
        )

        if data["BidVolume2"] or data["AskVolume2"]:
            tick.bid_price_2 = adjust_price(data["BidPrice2"])
            tick.bid_price_3 = adjust_price(data["BidPrice3"])
            tick.bid_price_4 = adjust_price(data["BidPrice4"])
            tick.bid_price_5 = adjust_price(data["BidPrice5"])

            tick.ask_price_2 = adjust_price(data["AskPrice2"])
            tick.ask_price_3 = adjust_price(data["AskPrice3"])
            tick.ask_price_4 = adjust_price(data["AskPrice4"])
            tick.ask_price_5 = adjust_price(data["AskPrice5"])

            tick.bid_volume_2 = data["BidVolume2"]
            tick.bid_volume_3 = data["BidVolume3"]
            tick.bid_volume_4 = data["BidVolume4"]
            tick.bid_volume_5 = data["BidVolume5"]

            tick.ask_volume_2 = data["AskVolume2"]
            tick.ask_volume_3 = data["AskVolume3"]
            tick.ask_volume_4 = data["AskVolume4"]
            tick.ask_volume_5 = data["AskVolume5"]

        self.gateway.on_tick(tick)
```

``` python
    def on_tick(self, tick: TickData) -> None:
        """
        Tick event push.
        Tick event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_TICK, tick)
        self.on_event(EVENT_TICK + tick.vt_symbol, tick)
```

``` python
    def on_event(self, type: str, data: Any = None) -> None:
        """
        General event push.
        on_event是gateway接收到信息之后的操作:
        将相应的事件和数据形成event,压入event_engine的队列.
        """
        event = Event(type, data)
        self.event_engine.put(event)
```		

gateway只会把返回的tickData压入事件引擎的队列，并不出去处理他。
所以还需要应用来接受EVENT_TICK事件，并提供处理方法。

搜索register(EVENT_TICK,可以看见每一个app的engine中都提供了处理tick的方法，并在appengine中进行注册。

### 2.1.1 极简订阅模块
``` python
#%% 极简模块订阅行情
from vnpy.event import EventEngine, Event
from vnpy.trader.event import EVENT_TICK
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange
import time
ctp_setting_simnow = {
#.......
}

#1 处理Tick事件的函数
def process_tick_event(event: Event) -> None:
    """
    Process log event.
    """
    tick = event.data
    print('{}'.format(tick))

#2 事件引擎，注册函数，并启动引擎，初始化Gateway
event_engine = EventEngine()
event_engine.register(EVENT_TICK,process_tick_event)
event_engine.start()
cg = CtpGateway(event_engine, "CTP")
cg.connect(ctp_setting_simnow) #登陆信息

time.sleep(5)
sreq = SubscribeRequest("ag2112",Exchange.SHFE)
cg.subscribe(sreq)

# TickData(gateway_name='CTP', symbol='ag2112', exchange=<Exchange.SHFE: 'SHFE'>
# , datetime=datetime.datetime(2021, 12, 10, 2, 30, 2, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
# , name='白银2112', volume=4486, turnover=0, open_interest=39462.0, last_price=4572.0, last_volume=0
# , limit_up=5093.0, limit_down=4167.0, open_price=4592.0, high_price=4598.0, low_price=4535.0, pre_close=4604.0
# , bid_price_1=4562.0, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0
# , ask_price_1=4580.0, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0
# , bid_volume_1=2, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0
# , ask_volume_1=4, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0, localtime=None)
```



