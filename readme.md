# WebCache-Server(Demo版）
## OverView
	
WebCache Demo Server是WebCache项目自带的一个简单的本地测试服务器，包含资源“上传”、“下载”、检查更新等主要功能。WebCache Demo Server主要服务于在应用WebCache SDK时，验证SDK应用是否成功，以及检验各项功能是否正常。下图简单描述了适应于些Demo Server的WebCache框架结构图：

![](http://7xqcm1.com1.z0.glb.clouddn.com/Demo-Webcache-Server-structure.png)

## 环境说明

 * 安装python3.5

   Mac OS上自带python解析器，但需确保是python3.x，如果不是，需要更新至python3.x版本
   
  这里不建议直接更新系统自带的python版本，可能会影响到你后续在使用python执行其他脚本时，出现python2.x与python3.x不兼容的问题。所以，简单点，直接安装python3.5后，不去更改原python的链接，而是新建一个链接指向可执行文件，如：python3，这样通过python3我们可以直接链向pytho3.5的目录，同时python命令仍然指向原系统版本。操作如下:
  
  
  ```
  /Library/Frameworks/Python.framework/Versions/3.5
  是它的默认安装路径，如果你的安装路径不是这个，需要相应改成你自己的安装路径
  
  sudo ln -s /Library/Frameworks/Python.framework/Versions/3.5/bin/pydoc3.5 /usr/bin/pydoc3
  sudo ln -s /Library/Frameworks/Python.framework/Versions/3.5/bin/python3.5 /usr/bin/python3
  sudo ln -s /Library/Frameworks/Python.framework/Versions/3.5/bin/pythonw3.5 /usr/bin/pythonw3
  sudo ln -s /Library/Frameworks/Python.framework/Versions/3.5/bin/python3.5m-config /usr/bin/python-config3
  ```
   
   
 * 下载Demo-Webcache-Server包。解压之后目录结构如下：

  ![](http://7xqcm1.com1.z0.glb.clouddn.com/%E7%9B%AE%E5%BD%95%E7%BB%93%E6%9E%84.png)
  
  * packages_dema目录下是webcache-server相关的python脚本。可以进入此目录，直接通过下面命令启动server:
	  
	  ```
	  python3 http_server.py
	  ```
	  
	  同时，需要更改测试的App(CCDemo）中的webcache server地址
	  
	  ```
	  config.serverAddress = @"127.0.0.1:8080";
	  ```

	  首次启动server，会在此目录下创建一个本地的DB文件，此DB是用来存储上传res的版本信息的
		
  * upload_tools目录下面，包含upload.py，用来模拟本地“上传”操作
   		
   		```
		python3 upload.py
		```

		如果之前没有安装过python的**requests**和**pycrypto**模块的话，需要先安装这两个模块。
		
		```
		sudo python3 -m pip install requests
		sudo python3 -m pip install pycrypto
		```

		如果在使用pip安装时，有问题，可以参考[同时装了Python3和Python2，怎么用pip](https://www.zhihu.com/question/21653286)
  		
  * test_packages目录下，包含几个测试用的资源包。
  		  		
 * 文件下载server。通过python提供的SimpleHTTPServer module，直接在本地启动一个httpServer，将文件目录映射到本地的某一目录，这里为了统一和方便，请<font color='red'>确保运行SimpleHTTPServer的目录与upload.py保持在同一路径</font>
 
  	```
 	cd .../upload_tools
 	python -m SimpleHTTPServer
 	```
 
## upload-tool使用说明

这里，“上传”只是模拟的本地上传行为，即资源包会拷到SimpleHttpServer所映射的文件目录下，然后执行一次upload的http请求，将对应res包的版本信息更新到DB里面去。

* 在upload-tool文件夹下，运行**python -m SimpleHTTPServer**（<font color='red'>确保在SimpleHTTPServer的运行路径与upload-tool相同，否则不保证后续操作的正确性</font>)
* 在Demo-Webcache-Server/packages_dema下，运行**python http\_server.py**
* 生成资源zip包
* 修改upload.py脚本，指明需要“上传”的本地资源zip包的路径，resID，resVersion(<font color='red'>请自行确保resID，resVersion, zipPath，domain的正确性</font>)。

	```
	config_items = {
    "resID": "login",  			//资源ID，可根据自己的res进行修改
    "resVersion": "20160321",	//资源版本，每次更新版本上传时要修改
    "appID": "kaola", 			//资源所在的appID，首次配置app资源时修改
    "domain": "www.baidu.com,www.163.com", //资源命中的domains，每次改变都需要修改
    "zipPath": "/Users/hzhehui/workspace/web-cache/test/login_20160321.zip",	//待上传资源包的本地地址
	}
	```
* 执行python3 upload.py，完成上传“请求”

上传成功的结果描述：

* upload.py输出打印信息：{"data": {"insert_cnt": 1}, "errMsg": "ok", "code": 200}
* upload_tools/packages目录下出现对应的资源包以及diff包
* DB中的versionInfo表中会增加一条新的记录

## Demo-Server测试

运行集成web-Cache的App，通过上述upload-tool一节描述的资源上传方式，进行一次资源的上传（红色标注表明在执行上传upload脚本时，需要更改的项）。

如：
	
```
config_items = {
    "resID": "login",
    "resVersion": "20160702",
    "appID": "kaola",
    "domain": "www.baidu.com,www.163.com",
    "zipPath": "/Users/h zhehui/workspace/web-cache/test/login_20160702.zip"
}
```


1.配好上述资源包login_20160702.zip后，更改<font color='red'>resID、resVersion、appID、domain、zipPath</font>，通过upload.py模拟上传。

2.打开类似Charles等抓包工具抓包。启动App。这时可以看到api/version_check/webapp的请求，对应的response:

```
{
	"data": {
	"resInfos": [
  	{
    	"userData": "{\"domains\": [\"www.baidu.com\", \"www.163.com\"]}",
    	"fullMd5": "13c118e8c0284c0f968883a554bb9dd0",
    	"resID": "login",
    	"state": 3,
    	"resVersion": "20160702",
    	"fullUrl": "http://localhost:8000/packages/login_20160702.zip"
	}]
	},
	"code": 200,
	"errMsg": "OK"
}

```

3.可以再进行一次资源更新的测试：
	
```
	config_items = {
	    "resID": "login",
	    "resVersion": "20160703",
	    "appID": "kaola",
	    "domain": "www.baidu.com,www.163.com",
	    "zipPath": "/Users/hzhehui/workspace/web-cache/test/login_20160703.zip",
	    "root_url": "http://localhost:8000/packages"
	}
```
		
配好新的资源包login_20160703.zip，更改<font color='red'>resID、resVersion、appID、domain、zipPath</font>，执行upload.py，模拟上传。


4.可再次启动App,这时可以看到api/version_check/webapp的请求，对应的response:

```
{
  "data": {
    "resInfos": [
      {
        "userData": "{\"domains\": [\"www.baidu.com\", \"www.163.com\"]}",
        "fullMd5": "9c5a25ced1728d78518e096e9a00bdfb",
        "resID": "login",
        "diffMd5": "5250bcf52d7e259bc4cdd0a12cc059e9",
        "resVersion": "20160703",
        "fullUrl": "http://localhost:8000/packages/login_20160703.zip",
        "diffUrl": "http://localhost:8000/packages/login.diff",
        "state": 1
      }
    ]
  },
  "code": 200,
  "errMsg": "OK"
}
```

