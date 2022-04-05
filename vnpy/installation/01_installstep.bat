:: vitual environment
:: 安装了虚拟环境时，留意python的搜索路径
:: ipython会搜索anaconda主目录下的.pth
:: python 只会在其虚拟文件夹的目录搜索
conda create -y -n vnpy270 python=3.7


conda activate vnpy270

cd C:\base\quantbase\vnpy\vnpy-master


:: Upgrade pip & setuptools
python -m pip install --upgrade pip setuptools

::Install prebuild wheel
python -m pip install https://pip.vnpy.com/colletion/TA_Lib-0.4.17-cp37-cp37m-win_amd64.whl

::Install Python Modules
:: many installation will be disconnected by fucking bad net connection
:: repeat it.
python -m pip install -r requirements.txt

:: Install vn.py
python -m pip install .


cd ./examples/vn_trader

python run.py