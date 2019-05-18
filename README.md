# TellMeWhere

> 小吐槽：一开始只是想弄一个傻瓜无脑式的信息收集工具，但是越写到后面突然醒悟，有些肮脏的搜索居然是 POST 方法，写着写着突然发现，居然有直接 API 返回结果的搜索引擎（抽根烟冷静冷静.jpg）隐隐在颤抖，要不要继续写下去，前面都还有什么肮脏无耻的障碍。工作两天感觉想通了，继续，omg，居然有的搜索引擎隐藏了源链接！omg，有的搜索引擎居然，每页返回的结果数不一样！！omg，异步太快被ban了......修修改改，缝缝补补又是一天<br/><br/>
在这里向 scrapy 大佬致敬。醒悟了，我为我的愚蠢郑重的面壁，没有办法拯救小白，我要好好更正思想。

# 概览

因为在工作中总是会碰到一些信息收集的任务，为尽可能的能找到更多经常翻翻查查各种搜索语法资料，过程很枯燥，重复性高，而且可能是各个站点变化太快的原因，网上没有找到一个比较完整的信息收集工具，于是乎就有了自己弄一个的想法。

一个异步的互联网信息收集工具，操作已尽可能傻瓜化，目前支持导出 json 格式，源代码很简单，希望有人能给我提出一些建议，现在脑子有点乱。

# 快速开始

### 要求

+ Python 3.5.2+
+ 工作于 Linux, Windows, Mac OSX, BSD

### 构建

```
git clone https://github.com/0xn0ne/TellMeWhere.git
python install -r requirements.txt
```

### 使用方法

**参数**

```
可选参数：
  -h, --help            显示帮助页面
  -e [name [name ...]], --engine [name [name ...]]
                        指定要调用的搜索引擎
  -o [number [number ...]], --output [number [number ...]]
                        输出的结果的内容格式
  --start number        开始搜索的页数
  --end number          结束搜索的页数
```

**样例**

```bash
# 显示帮助页面
python tmw.py -h

# xxx 关键字搜索
python tmw.py --keyword xxx

# xxx 关键字搜索，开始页数为 3
python tmw.py --start 2 --keyword xxx
```

### 搜索引擎

你可以自定义搜索引擎，引擎配置目前为 json 格式，目前内置 google, bing, bing_cn, baidu, github, pansou, wowenda 这些站点的简单搜索规则

一个搜索引擎为一个对象，可同时配置多个搜索引擎，如下：

```json
[
  {
    "protocol": "HTTP",
    "name": "example",
    "method": "GET",
    "url": "http://example.com/search",
    "query": {
      "wd": {
        "type": "key",
        "value": [
          "{keyword}"
        ]
      },
      "page": {
        "type": "pages",
        "value": 1
      }
    },
    "selector": "xpath",
    "parse": {
      "ul": {
        "selector": "//ul",
        "child": {
          "title": "//*[@class=\"bt\"]/text()",
          "url": "//*[@class=\"bt\"]/a/@href",
          "brief": "//*[@class=\"sm\"]/a/text()"
        }
      }
    },
    "headers": {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"
    },
    "body": null,
    "proxies": null
  }
]
```

**引擎配置说明**

+ protocol 请求协议
+ name 引擎名称，该名称会被识别到命令行 -e 参数的可选项中
+ method 请求方法
+ url 请求的链接，带或不带参数都可以
+ query 链接中查询输入部分，每个键表示一个查询输入键
  + type 这个查询键的类型。
    + key 表示一个是搜索关键字列表，搜索链接会根据列表来生成，列表内可以带参数，使用 "{xxx}" 表示参数，xxx 会被识别到命令行帮助信息中
    + pages 表示翻页步长
    + const 表示常量
  + value 查询输入的值
+ selector 表示解析引擎，目前可使用 xpath、api
+ parse xpath 的解析语法
+ headers 自定义的请求头
+ body POST、PUT 方法的主体部分
+ proxies 请求代理

佛祖保佑！
