# installation for QUANTAXIS
1. 
cd d:\uat\quant
git clone https://github.com/yutiansut/quantaxis --depth 1

2. 
conda create -n=qa
conda activate qa
conda install python=3.6

3. 
d:
cd D:\uat\quant\quantaxis
python -m pip install -r requirements.txt
python -m pip install tushare
python -m pip install pytdx
python -m pip install peakutils
python -m pip install patsy
python -m pip install jqdatasdk
python -m pip install -e .

4. 
cd D:\uat\MongoDB\Server\3.4\bin
.\mongod.exe --dbpath  D:\uat\quant\quantdata\data  --logpath D:\uat\quant\quantdata\log\mongo.log --httpinterface --rest --serviceName 'MongoDB'  -install
net start MongoDB

