# TellMeWhere

# 概览

一个异步的互联网信息收集工具，支持添加自定义引擎，引擎可自定义命令，自定义存储方式。

# 快速开始

### 要求

+ Python 3.5.2+
+ 工作于 Linux, Windows, Mac OSX

### 运行前工作

```
git clone https://github.com/0xn0ne/TellMeWhere.git
python install -r requirements.txt
```

### 使用方法

**参数**

```
必要参数
-e name [name ...], --engine name [name ...]
                    指定使用的收集引擎，可一次指定多个引擎

可选参数：
-h, --help          显示帮助信息
-p [url [url ...]], --proxies [url [url ...]]
                    设置 HTTP/HTTPS/SOCKS4/SOCKS5 代理，可使用多个。若指定文件路径如：file:///User/Ubuntu/proxy.txt，程序会读取文件中的代理
```

**样例**

```bash
# 显示帮助页面
python tmw.py -h

# 使用 crawler 引擎收集信息，检测 http://www.httpbin.org 页面中存在 admin 或 email 或 login 关键字的页面
python tmw.py -e crawler -ck admin email login -cu http://www.httpbin.org

# 使用 crawler 引擎收集信息，读取 url.txt 文件中的地址，读取 file:///User/Ubuntu/key.txt 中关键字，页面中存在这些关键字则记录
python tmw.py -e crawler -ck file:///User/Ubuntu/key.txt -cu file://url.txt
```

# API 简写

### class HttpEngine

在该类中主要执行网络请求，数据处理，存储调用等一系列 HTTP 从请求到存储关键数据的过程。

属性：
+ name：引擎的名称（需自定义）
  + 该处的内容会添加到命令行帮助中，方便使用者调用
+ args：自定义引擎的参数（可自定义）
  + 该处的内容会直接传入 `argparse.ArgumentParser()` 实例的 `add_argument` 方法中
  + ！注意：若出现重复的参数，会出现覆盖的情况
+ proxies：代理列表（可自定义）
  + 可手动设置该属性，`-p` 参数会添加到该列表中
+ input_args：用户输入的参数（不可自定义）
+ requested_url：请求过的 url（不可自定义）
+ session：`aiohttp.ClientSession` 实例（不可自定义）

方法：
+ coroutine startup()
  + 启动引擎的时候所做的预处理，该处需进行自定义
  + 生成 `base.Request` 到预备请求列表中
+ coroutine run()
  + HTTP 引擎运行的主体，里面会设置好可携带代理的 session
+ coroutine request_filter(request)
  + 过滤重复的请求，默认对 url 进行过滤
  + 参数：
    + request：`base.http.Request` 实例
  + 返回布尔值，如果已存在则返回 True，反之返回 False
+ coroutine request_handler(request)
  + 处理待请求列表中的 Request 实例，发出网络请求
  + 参数：
    + request：`base.http.Request` 实例
+ coroutine push_request(request)
  + 添加 `base.http.Request` 实例到待请求列表中
  + 参数：
    + request：`base.http.Request` 实例
+ coroutine process(response, request)
  + 对响应内容进行处理，该处需进行自定义
  + 参数：
    + response：`aiohttp.ClientResponse` 实例
    + request：`base.http.Request` 实例
  + 生成 `base.Request` 实例会被添加到预备请求列表中，生成其它内容会被传入 `self.storage()` 函数中
+ coroutine parse(text, request, selector_type, selector)
  + 解析工具，会根据 selector 将解析结果与规则的 key 对应上
  + 参数：
    + text：带解析的文本内容
    + request：`base.http.Request`，记录解析来源
    + selector_type：解析器名称，事实上该参数没用
    + selector：解析规则，应为一个 map 对象，若有一个 map 为 `{"box": "//a/@href"}`，会根据 `//a/@href` 解析出所有符合该 xpath 规则的结果：`{"box": ["http://some1", "http://some2"], "source": "source_link"}`，`source` 表示来源页面，可以添加子解析。`{"box": {"selector": "//ul/li", "child": [{"c_box1": "//a/@href"}, {"c_box2": "//a/text()"}]}}`
    + 返回解析结果
+ coroutine storage()
  + 存储数据使用
