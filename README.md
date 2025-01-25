## Introduction 简介

A small local server for ```Groove Coaster 2: Original Style```, implemented with ```Python``` and ```Flask```. Supports asset delivery (paks and song/stage files) and basic shop, which unlocks content via Groove Coin (a removed feature in-game). Support save file backup using a recreation of the TAlT0 ID system. Supports account whitelisting and banning. Does not support mission, status, and leaderboard as of now (score submissions are saved in the database). Tested on Android/ios 1.0.18 client.

This project is for game preservation purposes only. This github repo does not contain any proprietary code or content. It is provided as-is.

You are not allowed to use it for commercial purposes. You shall bare all the responsibility for any potential consequences as a result of running this server. If you do not agree to these requirements, you are not allowed to replicate or run this program.

Inspiration: [Lost-MSth/Arcaea-server](https://github.com/Lost-MSth/Arcaea-server)

Special thanks: [Walter-o/gcm-downloader]https://github.com/Walter-o/gcm-downloader

Warning: Do not put personal files under the folders in the private server directory - all files within these sub-folders will be accessible by anyone with your server address!

一个基于```Python```和```Flask```的微型```Groove Coaster 2: Original Style```本地服务器。支持文件下载 (pak和谱面，歌曲文件)，基础的商店（使用GCoin解锁内容），和重做的TAlT0 ID系统支持的存档备份功能。支持账号白名单和封禁。不支持任务，状态，和排行榜（分数提交有被服务器记载）。通过安卓/ios1.0.18客户端测试。

此项目的目标是保持游戏的长远可用性 (game preservation)。此repo内没有任何侵犯知识产权的代码和文件。此项目在“按现状” (as-is) 条件下提供。

你不得将此项目用于商业行为。你应对因运行本服务器而产生的任何潜在后果承担全部责任。如果您不同意这些要求，则不允许您复制或运行该程序。

灵感: [Lost-MSth/Arcaea-server](https://github.com/Lost-MSth/Arcaea-server)

鸣谢: [Walter-o/gcm-downloader]https://github.com/Walter-o/gcm-downloader

警告：不要将私人文件放至私服内的文件夹里。自带的文件夹内所有文件都可被私服抓取！

## Download 下载

TBA

You need to get the CDN files from the game Server. I will not include this within this project as it is copyrighted material, and because it is quite sizable (3.7GB+ for Android only, double if including iOS). I will also not provide the script I used to scrape the website, as I don't want the developer to face a massive bill. If the game's server shuts down in the future, this might change. I will only provide the directory hierarchy to show you what is needed.

If you want to use the official client, you would need some proxying software to redirect the traffic to your server. If you are okay with modifying the client, you can connect directly and please read the next tutorial。

你需要从游戏服务器获取 CDN 文件。我不会将其包含在该项目中，因为它受版权保护，而且很大（安卓3.7GB+，ios加倍）。不会提供用来抓取网站的脚本，因为我不希望开发者收到巨额账单。如果游戏的服务器将来关闭，情况可能会改变。我只会提供目录层次结构来向您展示需要哪些文件。

<details>
<summary>File Structure 文件结构</summary>
<br>

server/

├─ files/

│  ├─ gc2/

│  │  ├─ audio/

│  │  │  ├─ ogg and m4a zips

│  │  ├─ stage/

│  │  │  ├─ zip files for stage

│  │  ├─ model.pak

│  │  ├─ skin.pak

│  │  ├─ tunefile.pak

│  ├─ web/

│  │  ├─ webpage assets

├─ fs.json

├─ 7001.py

├─ config.py

</details>

如果你想用官方的客户端和数据包，就需要用代理软件。如果你可以对安装包和数据包进行更改，就可以和私服直连，请看下一个教程。



## Instruction for Use (for official client) 原版安装包的使用说明

<details>
<summary>English</summary>
<br>

For android 9+ devices, you need to bypass the https protection in order to MITM the connection between game client and server. If you have root, you can install Certificate Authorities to system level, allowing the device to trust it. If you don't have root, I don't think it is possible and you might have to modify the client slightly using the next section.

I don’t have an iOS device, so I cannot test iOS compatibility. I've heard that https is enforced there, meaning the stack below likely won't work. You likely need a server, with a domain and SSL, to serve https from the get-go.

I will demonstrate the VProxid + Charles method. Install VProxid on your android device. Install Charles on your Windows PC. Charles has a free trial period, but there are ways to register it for free. Please do your own research on that subject.

Install python on your server machine. Download all the assets and server files. Run ipconfig in CMD to obtain your local IPV4, modify config.py to match the IP. In VProxid, create a new profile with server as the server IP, port as 8889, type as socks5, and in "click to select applications", select groove coaster 2. Go back and activate the profile.

Install Charles Certificate Authority on your android device by going to the top bar: Help – SSL Proxying – Install Charles Root Certificate on a mobile device. Follow its instructions. Install the downloaded certificate. If you want to use the first method, follow this (https://gist.github.com/pwlin/8a0d01e6428b7a96e2eb) guide to move the user-level certificate to system level. Once done, go to your system setting – certificates, and double check that Charles certificate appears at the bottom of the system certificates.

After you’re done, open command on windows. Type “ipconfig”, and remember your IPV4 address. This assumes that you are connected to a WIFI, and it should start with 192 or 172. Open the config.py of the private server, and change the IP accordingly. Type “cmd” in the file directory on the top of the file explorer, and press enter. A command prompt will be opened for that directory. Type “python 7000.py” to start the server. If an error pops up, resolve it now – install python for your machine, and install flask module.

In Charles, open top bar: Proxy – Proxy Settings. Enable SOCKS proxy on port 8889. Enable http proxying over socks, include default ports. Then, in top bar: Tools – Map Remote, map a URL to your Server IP address:port, under http. The URL is: https://gc2018.gczero.com. 

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help1.JPG)


![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/test2.JPG)

On your android device, open VProxid. Create a new profile, with the server being your computer’s IP, port being 8889, type being socks5, and select GROOVE 2 using the app selector. Once created, click the play button on the profile to activate it.

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help3.jpg)

Make sure the private server is running on your PC. Make sure Charles acknowledges the connection from the device. Make sure VProxid is running. Make sure your phone and laptop are under the same network. Start the game, and have fun.
</details>

<details>
<summary>中文</summary>
<br>

对于 Android 9+ 设备，您需要绕过 https 保护才能对游戏客户端和服务器之间的连接进行中间人攻击。 这可以通过至少两种方式完成： 如果您拥有 root 权限，则可以将证书安装到系统级别，从而允许设备信任中间人软件。 或者您可以补丁游戏的客户端数据包里的设置文件。

如果您使用的是 iOS，由于我没有iOS设备，所以无法测试iOS兼容性。我听说iOS强制https，意味着以下的方法可能不可行。你可能需要一个有域名和SSL的服务器来从源头使用https。

这里展示 VProxid 加 Charles 方法。 在您的 Android 设备上安装 VProxid。 在 Windows PC 上安装 Charles。 Charles 有免费试用期，但有多种方法可以免费注册。 请对此主题进行自己的研究。

在您的 Android 设备上安装 Charles 根证书：顶栏：帮助 – SSL 代理 – 在移动设备上安装 Charles 根证书。 按照其说明进行操作。 安装下载的证书。 如果您想使用第一种方法，请按照此 (https://gist.github.com/pwlin/8a0d01e6428b7a96e2eb) 指南将用户级证书移至系统级。 完成后，转到系统设置 - 证书，并仔细检查 Charles 证书是否出现在系统证书页面底部。

完成后，在 Windows 上打开cmd。 输入“ipconfig”，并记住您的 IPV4 地址。 这里假设你连接到了WIFI，IP应该以192或172开头。打开私服的config.py，并相应地更改IP。 在文件资源管理器顶部的文件目录中输入“cmd”，然后按 Enter。 将打开该目录的命令提示符。 输入“python 7000.py”启动服务器。 如果弹出错误，请立即解决 - 为您的计算机安装 python，安装 Flask 和 sqlite3 模块。

在 Charles 中，打开顶部栏：Proxy – Proxy Settings。 在端口8889上启用SOCKS代理。通过socks启用http代理，包括默认端口。然后，在顶部栏中： Tools – Map Remote，将URL映射到您的服务器IP:端口（http 下）。URL为：https://gc2018.gczero.com。

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help1.JPG)


![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/test2.JPG)

在您的 Android 设备上，打开 VProxid。 创建一个新的配置文件，服务器为您计算机的 IP，端口为 8889，类型为socks5，然后使用应用程序选择器选择 GC2。 创建后，单击配置文件上的播放按钮将其激活。

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help3.jpg)

确保您的 PC 上正在运行私服。 确保 Charles 提示并正在接收来自设备的连接。 确保 VProxid 正在运行。 确保您的设备和电脑在同一网络下。 开始游戏吧。


</details>

## Instruction for Use (For modified client) 改版安装包的使用说明

<details>
<summary>English</summary>
<br>

By modifying the apk's obb verification function and `obb`'s `settings.cfg`, you can connect to the server without using any proxy software. To do so, decompile `classes.dex` using your favorite `smali` decompiler, and go to `jp.co.groovecoasterzero/BootActivity`. Delete the part in `e()` where the loop is checking for a size, and, if mismatch, override a variable that causes the code to branch into `DownloadActivity`. We want the game to load the obb regardless of its size.

After this, open the game's `obb` with password `eiprblFFv69R83J5`, extract everything, open `settings.cfg`, and edit the `serverUrl` to the `http://ip:port/` of your server. Compress every file with `WinRAR` to zip, using the password to encrypt it. Use `ZIP legacy encryption`. Override the `obb` in `Android/obb/jp.co.groovecoasterzero` and you should be able to connect directly. Just start the game and observe the server.

With iOS, none of the above is necessary as the installation package is a single .ipa. Just edit `settings.cfg` and sideload the ipa.
</details>

<details>
<summary>中文</summary>
<br>

你可以通过修改apk里的obb校验函数然后修改`obb`里的`settings.cfg`来直连私服，无需中继软件。用顺手的`smali`反编译器来反编译`classes.dex`，然后去`jp.co.groovecoasterzero/BootActivity`。删除`e()`里循环检查文件大小的部分。这部分会检查obb文件的大小，如果不一致会修改一个变量跳至`DownloadActivity`。我们想强制游戏读取。

然后打开游戏的`obb`，密码是`eiprblFFv69R83J5`。提取全部文件，打开`settings.cfg`，将`serverUrl`改成私服的`http://ip:端口/`。用`WinRAR`压缩全部文件至zip，用密码加密。用`ZIP legacy encryption`。覆盖`Android/obb/jp.co.groovecoasterzero`里的`obb`，应该就可以直连了。打开游戏，观察私服的输出。

iOS简单得多，只要修改ipa中的`settings.cfg`并侧载即可。
</details>


## Admin Function 管理员功能

Database can be opened with DB Browser.

If you want to make your service only available to whitelisted devices, turn on ```AUTHORIZATION_NEEDED``` in ```config.py``` and add the device id after the .php request to the ```whitelist table```. If you want to ban a device/taito ID, add the device ID or the username of the taito ID to the blacklist table. The ```reason``` column is for your own reference. If a device is logged in to that Taito ID, they cannot download asset, cannot log out, and cannot change name. If a device is not in the whitelist (if enabled) or is banned by device ID, they will not be able to download anything.

数据库可以用DB Browser打开。

如果你想只对在白名单里的设备提供服务，开启```config.py```里的```AUTHORIZATION_NEEDED```，并将.php请求后面的设备ID加入```whitelist```列表。如果你想封禁设备或者Taito ID，将设备ID或者用户名加入```blacklist```列表。```reason```列可供你记录封禁原因。如果设备登陆该Taito ID，它将无法下载数据，不能登出，而且不能改名。如果设备在白名单开启后不在白名单里，或者设备被封禁，它将无法下载任何东西。

## About Account Implementation 关于账号设置

Account is only used for save file saving/loading (song ownership and coins are tied to devices. However, songs unlocked in the save file will remain unlocked on a new device). Unlike the official version, you can rename and log out of your account. However, only one device may be connected to an account at a time. The old device will be logged off if a new device logs in.

账号仅用于保存/同步存档。Gcoin和歌曲所有权和设备绑定。不过，存档中已经解锁的曲目将在新的设备上可用。官方版不允许重命名及登出账号。私服则可以进行这些操作。不过，一个账号只能同时登陆一台设备，如果登录第二台设备，第一台设备将被挤掉。

## Logical next step 接下来。。。

### SAVE NETWORK PACKETS!!!

Implement leaderboard, personalization (title), maybe mission. 1:1 representation of the offical server is nigh impossible for my skill level. Those features are glorified web pages.

Porting charts from PC and 4MAX to mobile. Once figuring out stage_param.dat, this should be quite easy...

### 赶 紧 抓 包 ！ ！ ！

实装排行榜，title个性化，甚至任务。官服1：1还原对我来说太难了。毕竟这些功能实际上不是游戏，而是网页。

将pc版和4max歌曲加入2OS. 琢磨透stage_param.dat之后，应该就是轻而易举的了。


