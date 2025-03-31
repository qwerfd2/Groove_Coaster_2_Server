# Groove-Coaster-2OS-Server

A small local server for `Groove Coaster 2: Original Style`, implemented with `Python` and `Flask`. 

一个基于`Python`和`Flask`的微型`Groove Coaster 2: Original Style`本地服务器。

<details>
<summary>English</summary>
<br>

## Introduction

This project is for game preservation purposes only. Creative liberty and conveniences have been taken when it comes to specific implementation. The goal is not to ensure 1:1 behavior, but to guarrantee the minimum viability of playing this game. It is provided as-is, per the MIT license.

You are not allowed to use it for commercial purposes. You shall bare all the responsibility for any potential consequences as a result of running this server. If you do not agree to these requirements, you are not allowed to replicate or run this program.

Inspiration: [Lost-MSth/Arcaea-server](https://github.com/Lost-MSth/Arcaea-server)

Special thanks: [Walter-o/gcm-downloader](https://github.com/Walter-o/gcm-downloader)

Warning: Do not put personal files under the folders in the private server directory - all files within these sub-folders will be accessible by anyone with your server address! Security and performance are not guaranteed, and it is not recommended to host this server on the internet. You have been warned.

### Supported Features

| Features            | Degree of support                                                                                                      |
|---------------------|------------------------------------------------------------------------------------------------------------------------|
| Asset delivery      | .pak, stage and music zip files                                                                                        |
| Shop                | Purchase individual songs, avatars, and items using GCoin. GCoins are earned by playing the game. Does not support music preview. Does not support song pack. |
| Ranking             | Individual song-difficulty ranking. Support total score ranking, but does not support regional ranking. Does not support viewing player profile.        |
| Save backup         | Support save/load via an Account system. Support password and username changes. Support logging out.                   |
| Titles              | Static full-unlock and setting titles via "Status".                                                                    |
| Mission             | Basic automatic song unlock after reaching in-game levels. Everything else is not supported.                           |
| Friend              | Not supported.                                                                                                         |
| Progress Grid       | Not supported.                                                                                                         |
| Additional features | Account/device whitelisting and banning.                                                                               |

## Download

Server download: Download the project as zip. To do so, click the green `Code` button on the top, then `Download ZIP` at the bottom of the popup.

Asset download: [MEGA](https://mega.nz/folder/frxWHRrQ#v6tth7Zo5rrj9foDhGYCBA) [Google Drive](https://drive.google.com/drive/folders/1rTSLs2DTV8AYVitPULlBErou3Q8KLydM?usp=sharing) [Baidu(code: aaaa)](https://pan.baidu.com/s/1YVFfKBq1ULOgCkdrVQhFFg)

If you'd like to upload it somewhere else and contribute the link, please contact #AnTcfgss or QQ 3421587952， thanks!

Download `common.zip` and a platform of your choosing. Unzip the folders within to the private server root directory. If in doubt, check the `File Structure` section at the end.

### GC4MAX Expansion

To install the `GC4MAX` expansion, which ports arcade exclusive tracks, avatars, and skins to 2OS, download the `4max expansion` folder's `common.zip` and a platform of your choosing. Unzip the folders within to the privates server root directory. Overwrite existing files. Note that the included installation `apk` or `ipa` must be used for correct avatar rendering.

Edit `config.py`'s `MODEL`, `TUNEFILE`, and `SKIN` value to match the `pak`'s timestamp. `paks` can be found at `/files/gc2/`.

Important: You must use the `common.zip` inside the `4max expansion` folder, not the `common.zip` in the root directory.

#### Updates

The `GC4MAX` expansion will receive updates to fix bugs. You can check the latest version by going to the ingame `shop` - `songs page` - `GC4MAX banner` after purchasing the expansion. A server restart is required to fetch the latest update.

The server owner must install the update on their instance. They can download it through the usual links. Simply download the `update-vx.zip` and unzip the content to the server root directory. Make sure to check the timestamp of the latest `pak` files and update them accordingly inside the `config.py`. A server restart is required after the installation.


## Dependencies

- Python

- Flask

- Crypto (pycryptodome)

- bcrypt

- requests

## At the Start

First, you need to set up the server. Use the `Setup the Server First` section.

Next, there are 2 ways to set up the connection. Pick one.

1. Proxy. Requires more setup, but the install package can remain unmodified.

2. File modification. Easier setup, but file edit is necessary.

For method 1, use the `Instruction for Use (for official client)` section.

For method 2, use the `Instruction for Use (For modified client)` section.

## Setup the Server First

### PC/MAC (Easier)

Download the server and assets, and extract everything according to the `Download` section.

Install `python` and `pip` on your PC/MAC. 

Note that MAC uses `python3`. Code examples in this document will use the default of Windows, which is `python`. After the installation, install dependencies using `pip install ...`.

Open command on Windows (MAC open terminal). Type `ipconfig` (MAC `ifconfig`), and obtain your IPV4 address. This assumes that you are connected to a WIFI, and it should start with 192 or 172.

Open the `config.py` of the private server, and change the `IP` accordingly.

Type `cmd` in the file directory on the top of the file explorer, and press enter. A command prompt will be opened for that directory.

Type `python 7001.py` to start the server. If an error pops up, resolve it now – did you install all the dependencies? Is the IP correct?

### Android (Harder)

<details>
<summary>Details</summary>
<br>

Install [Termux](https://github.com/termux/termux-app/releases).

Type the following commands.

`termux-setup-storage`

`pkg install python`

Use

`pip install ...`

to install `rust`, `flask`, `passlib`, `pycryptodome`, `requests`.

If ssl errors pop up, you might need to ``pkg up ssl -y``.

Copy the server to phone, or upzip the server files on the phone. (Skip the iOS files if not needed, it takes up a lot of space)

change `config.py`'s `IP` to `127.0.0.1` (this is `loopback`. Feel free to use your android device's `IPv4` via `ifconfig` if you are connected to a WIFI, to enable the server to the entire network).

`cd storage/shared/.... (server location on android file system)`

`python 7001.py` to start the server.

</details>

### iOS (Hard)

<details>
<summary>Details</summary>
<br>

I did some research on `Pythonista` and it seems possible, but you are on your own for this one.

</details>

## Instruction for Use (for official client) 

<details>
<summary>Details</summary>
<br>

### Android

For android 9+ devices, you need to bypass `https` in order to MITM the connection between game client and server. If you have root, you can install Certificate Authorities to system level, allowing the device to trust it. If you don't have root, I don't think it is possible and you might have to modify the client.

I will demonstrate the `VProxid` + `Charles` method.

Install `VProxid` on your `android` device.

Install `Charles` on your `Windows PC`. `Charles` has a free trial period, but there are ways to register it for free. Please do your own research on that subject.

Your server should already be running. 

Install `Charles Certificate Authority` on your `android` device by going to Charles UI `top bar`: `Help` – `SSL Proxying` – `Install Charles Root Certificate on a mobile device`. Follow its instructions. Install the downloaded certificate on the `android` device. Follow [this](https://gist.github.com/pwlin/8a0d01e6428b7a96e2eb) guide to move the user-level certificate to system level. Once done, go to the `android` device's `system setting` – `certificates`, and double check that `Charles` certificate appears at the bottom of the system certificates.

In `Charles`, open `top bar`: `Proxy` – `Proxy Settings`. Enable `SOCKS` proxy on port `8889`. Enable `http proxying over socks`, include default ports. Then, in `top bar`: `Tools` – `Map Remote`, map a URL to your Server `IP address:port`, under `http`. The URL is: `https://gc2018.gczero.com`. 

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help1.JPG)

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/test2.JPG)

On your `android` device, open `VProxid`. Create a new profile, with the server being `your computer’s IP`, port `8889`, type `socks5`, and select `GROOVE 2` using the app selector. Once created, click the play button on the profile to activate it.

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help3.jpg)

Make sure the private server is running on your PC. Make sure Charles acknowledges the connection from the device. Make sure VProxid is running. Make sure your phone and laptop are under the same network. Start the game, and ovserve the server.

### iOS

I did not test this method on iOS. If you know how to proxy stuff there, feel free read the Android guide and try the equivalent on iOS.

</details>

## Instruction for Use (For modified client) 

<details>
<summary>Details</summary>
<br>

### Android

Download the `apk` file from the link's `install packages` folder. Install it. For `Android 14+` devices, you might need to use `lucky patcher` to rebuild the app (`Menu of Patches` - `Create Modified APK File` - `APK with changed permissions and activities` - toggle `Removes integrity check and signature verification` and `Re-sign with original signature for android patch "Disable .apk Signature Verification"`).

This `apk` has been modified. If you'd like to edit it on your own, see the last paragraph.

Open the game's `obb` with password `eiprblFFv69R83J5`, and extract all the files. Or, download the extracted folder from the link's `install packages/main.76.jp.co.taito.groovecoasterzero.obb`.

Open `settings.cfg` with your text editor, and change `serverUrl` to your server's `http://ip:port/`.

Use `WinRAR` or `7-zip` to compress everything within the folder with the original password. Use `ZIP legacy encryption` for `WinRAR`, `ZipCrypto` for `7-zip`。Name the compressed zip to `main.76.jp.co.taito.groovecoasterzero.obb`.

Paste (overwrite) the `obb` already inside `Android/obb/jp.co.taito.groovecoasterzero`. If the folder does not exist yet, you need to create it manually.

Open the game and observe the server output.

(The provided apk has the following modifications. Skip if you are not interested in it)

By modifying the apk's obb verification function and `obb`'s `settings.cfg`, you can connect to the server without using any proxy software. To do so, decompile `classes.dex` using your favorite `smali` decompiler, and go to `jp.co.taito.groovecoasterzero/BootActivity`. Delete the part in `e()` where the loop is checking for a size, and, if mismatch, override a variable that causes the code to branch into `DownloadActivity`. We want the game to load the obb regardless of its size.

### iOS

Download the `ipa` package from the link's `install packages` folder.

Open the `ipa` file with your favorite zip viewer。Go into`Payload`,`GROOVE 2`. extract `settings.cfg`.

Open `settings.cfg` with a text editor，Edit `serverUrl` to your server's `http://ip:port/`.Drag`settings.cfg` back into the `ipa`。

Sideload the `ipa`. Open the game, and observe the server.

</details>

## Admin Functionalities

Database can be opened with DB Browser.

If you want to make your service only available to whitelisted devices, turn on `AUTHORIZATION_NEEDED` in `config.py` and add the device id after the .php request to the `whitelist table`. If you want to ban a device/taito ID, add the device ID or the username of the taito ID to the blacklist table. The `reason` column is for your own reference. If a device is logged in to that Taito ID, they cannot download asset, cannot log out, and cannot change name. If a device is not in the whitelist (if enabled) or is banned by device ID, they will not be able to download anything.

`getCrypt.py` is a standalone script used to decrypt the mass inside the `GET` requests.

## Account System Implementation

Account is only used for save file saving/loading (song ownership and coins are tied to devices. However, songs unlocked in the save file will remain unlocked on a new device). Unlike the official version, you can rename and log out of your account. However, only one device may be connected to an account at a time. The old device will be logged off if a new device logs in.

## Ranking System Implementation

I speculate that the official server's behavior hinges upon the fact that you cannot log out of your account, and that there is a maximum device count (5). This means that each `account` is connected to 5 `devices` via `foreign keys`, and the owned `entitlements` (stages, avatars, etc) and `play records` can be tallied.

In the private server, you can log out of devices with ease. This means that `entitlements` and `play records` is not possible to remain consistent, unless we treat `account` as `devices`, which is clearly not the offical behavior.

With the current setup, if a `device` is playing with an associated `account`, the `account` information is saved at the same time and will continue to be shown on ranking in the future. The `Avatar` information is saved with the `play records` and will not follow the `account` or `device`. The `Title` information is not in the `play records`, nor in the `account`, so it will be tied to the `Title` of the `device`.

## Ranking Data

A rather comprehensive data scrape was conducted prior to the server shutdown, containing at least first `99950` ranks of any given song. The data and metadata can be acquired at [Google Drive](https://drive.google.com/file/d/1tsZnRnxPdUAoFPLfCzuXJFf9GgHR6rGz/view?usp=drive_link)

Note that this data is for analytics only, and the functionality to embed this data inside the private server is not and will not be supported by me. Feel free to Fork and create your own implementation.

</details>

<details>
<summary>中文</summary>
<br>

## 简介

此项目的目标是保持游戏的长远可用性 (game preservation)。在具体实施上，我采取了一些便利及创意性的措施（偷懒）。此项目的目标不是确保 1:1 还原官服，而是保证游戏长久可玩。此项目在MIT许可证的“按现状” (as-is) 条件下提供。

你不得将此项目用于商业行为。你应对因运行本服务器而产生的任何潜在后果承担全部责任。如果您不同意这些要求，则不允许您复制或运行该程序。

灵感: [Lost-MSth/Arcaea-server](https://github.com/Lost-MSth/Arcaea-server)

鸣谢: [Walter-o/gcm-downloader](https://github.com/Walter-o/gcm-downloader)

警告：不要将私人文件放至私服内的文件夹里。自带的文件夹内所有文件都可被私服抓取！安全性和效率无法保证，不建议在公网上搭建。这不是强制要求，不过别怪我没提醒过你。

### 支持的功能

| 功能         | 支持程度                                                                                     |
|--------------|---------------------------------------------------------------------------------------------|
| 文件下载      | .pak, 谱面及音频zip文件                                                                      |
| 商店         | 用GCoin购买单独的歌曲，头像，和道具。 GCoins可通过玩游戏来获得。不支持音频预览。不支持曲包。       |
| 排行榜       | 每首歌曲/难度的单独排行榜。总分排行榜。不支持地区排行榜。不支持查看其他玩家的详细信息。            |
| 存档备份     | 支持通过账号系统的保存/加载。支持修改密码和用户名。支持登出。                                     |
| Titles      | 通过Status观看并使用全解锁的Titles。                                                           |
| 任务         | 支持达到游戏内经验等级后歌曲自动解锁。其他功能均不支持。                                         |
| 好友         | 不支持。                                                                                     |
| 进度表       | 不支持。                                                                                     |
| 其他功能     | 账号/设备白名单和封禁。                                                                       |

## 下载

服务器下载：将此repo以zip形式下载。点击上栏绿色的`Code`按钮，然后点击弹窗下面的`Download ZIP`按钮。

资源下载：[MEGA](https://mega.nz/folder/frxWHRrQ#v6tth7Zo5rrj9foDhGYCBA) [Google Drive](https://drive.google.com/drive/folders/1rTSLs2DTV8AYVitPULlBErou3Q8KLydM?usp=sharing) [Baidu(密码aaaa)](https://pan.baidu.com/s/1YVFfKBq1ULOgCkdrVQhFFg)

如果你想将资源备份到别的网盘并贡献链接，请联系#AnTcfgss or QQ 3421587952，感谢！

下载 `common.zip` 和您设备的平台。将里面的所有文件夹解压到服务器根目录。如有疑惑，请参照文末`文件结构`章节。

## GC4MAX扩展包

如想下载`GC4MAX`扩展包（包含了街机独占曲目，皮肤，和角色），下载`4max expansion`里的`common.zip`和和您设备的平台。将里面的所有文件夹解压到服务器根目录。如有重复，覆盖所有文件。请注意，必须使用包含的`apk`或`ipa`安装包来正确渲染角色。

修改`config.py`的`MODEL`, `TUNEFILE`, and `SKIN` 值至现有`pak`文件的时间戳. `paks`文件的位置在`/files/gc2/`.

重要: 必须使用`4max expansion`文件夹里的`common.zip`，而不是根目录里的`common.zip`.

#### 更新

`GC4MAX` 扩展包会不定期接受bug修复更新。你可以在购买扩展包之后，通过游戏内的 `shop` - `songs 页面` - `GC4MAX 标题图片` 来查看最新的版本。为获取最新的版本更新，服务器应当不定期重启。

服务器拥有者需要在TA的系统上安装更新。他们可以通过以往的链接下载更新文件。下载 `update-vx.zip` 并将所有内容解压至服务器根目录。确保最新的 `pak` 时间戳已在 `config.py` 里更新。安装完成后，需要重启服务器。

## 环境依赖

- Python

- Flask

- Crypto (pycryptodome)

- bcrypt

- requests

## 如何开始

首先，你需要配置服务器。请使用`配置服务器`。

接下来，有两种方式来设置连接。选一个吧。

1. 代理。需要更多配置，不过安装包不需要修改。
   
3. 修改文件。配置更加简单，不过。。必须修改文件。

方法1，请使用`原版安装包的使用说明`。

方法2，请使用`改版安装包的使用说明`。

## 配置服务器

### PC/MAC(简单)

按照`下载`章节来下载解压服务器和资源。

PC/MAC安装 `python`，安装 `pip`。

注意 MAC 默认为 `python3`。往后的示例默认用 windows 的默认，即 `python`。安装完成后，使用
`pip install ...`安装所有依赖项。

PC打开 `cmd` 输入 `ipconfig`。MAC 打开 `terminal` 输入 `ifconfig`。获得你的`IPV4`,一串为192或172开头的数字。

PC用文本编辑器打开服务器文件夹的 `config.py`，将`IPV4`填写至`IP`。`PORT`(端口)也可以更改。

文件管理器上方的文件夹路径清空，输入 `cmd`。命令行窗口会弹出。

输入 `python 7001.py`来开启服务器。如果出现错误，就解决他们吧。检查依赖项是否安装，网络配置是否正确。

### 安卓(稍难)

<details>
<summary>细节</summary>
<br>

安装 [Termux](https://github.com/termux/termux-app/releases).

输入下面的命令。

`termux-setup-storage`

`pkg install python`

用

`pip install ...`

来安装 `rust`, `flask`, `bcrypt`, `pycryptodome`, `requests`.

如果出现ssl问题，可能需要``pkg up ssl -y``.

将服务器拷到手机上，或者在手机上解压服务器文件。（如不需要iOS文件，就省点手机空间，别拷贝ios的东西了）

修改 `config.py` 的 `IP` 至 `127.0.0.1` (这是 `本地回环`。如果连接了WIFI，可以使用`ifconfig` 获取手机的 `IPv4` 并填入，以在整个网络下支持私服).

`cd storage/shared/.... (服务器在安卓文件系统的位置)`

`python 7001.py` 来运行服务器。

</details>

### iOS (难)

<details>
<summary>细节</summary>
<br>

`Pythonista`貌似可用，不过我祝你好运。

</details>

## 原版安装包的使用说明

<details>
<summary>细节</summary>
<br>

### 安卓

对于 Android 9+ 设备，您需要绕过 `https`才能对游戏客户端和服务器之间的连接进行中间人攻击。如果您拥有 root 权限，则可以将证书安装到系统级别，从而允许设备信任中间人软件。若您没有root，此方法可能不可用。

这里展示`VProxid`加`Charles`方法。 在您的`Android`设备上安装`VProxid`。 在`Windows PC`上安装`Charles`。 `Charles`有免费试用期，但有多种方法可以免费注册。 请对此主题进行自己的研究。

你的服务器应该已经在运行。

在您的`Android`设备上安装`Charles 根证书`：Charles用户界面`顶栏`：`Help` – `SSL Proxying` – `Install Charles Root Certificate on a mobile device`. 按照其说明进行操作。`Android`设备上安装下载的证书。请按照此[指南]((https://gist.github.com/pwlin/8a0d01e6428b7a96e2eb))将用户级证书移至系统级。 完成后，转到系统设置 - 证书，仔细检查`Charles`证书是否出现在系统证书页面底部。

在`Charles`中，打开顶部栏：`Proxy` – `Proxy Settings`。 在端口`8889`上启用`SOCKS`代理。打开``http proxying over socks``，配置默认端口。然后，在顶部栏中： `Tools` – `Map Remote`，将如下`URL`映射到`服务器IP:端口`（http协议）。URL为：`https://gc2018.gczero.com`。

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help1.JPG)


![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/test2.JPG)

在您的`Android`设备上，打开`VProxid`。创建一个新的配置文件，服务器为`您计算机的IP`，端口为`8889`，类型为`socks5`，然后使用应用程序选择器选择`GROOVE 2`。 创建后，单击配置文件上的播放按钮将其激活。

![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/help3.jpg)

确保您的`PC`上正在运行私服。 确保`Charles`提示并正在接收来自设备的连接。 确保`VProxid`正在运行。 确保您的设备和电脑在同一网络下。 开始游戏吧。

### iOS

我不了解iOS系统，如果你了解ios的代理软件，可以阅读安卓部分，然后照葫芦画瓢（

</details>

## 改版安装包的使用说明

<details>
<summary>细节</summary>
<br>

### 安卓

下载网盘里`install packages`里的`apk`文件。安装。`安卓14+` 设备可能需要用`幸运破解器`重构APK (`Menu of Patches` - `Create Modified APK File` - `APK with changed permissions and activities` - 打开 `Removes integrity check and signature verification` 和 `Re-sign with original signature for android patch "Disable .apk Signature Verification"`)。

此`apk`被修改过。若想自己修改,请看最后一段。

打开游戏的`obb`，密码是`eiprblFFv69R83J5`。提取全部文件。或者，从网盘下载`install packages/main.76.jp.co.taito.groovecoasterzero.obb`.

用文本编辑器打开`settings.cfg`，将`serverUrl`改成私服的`http://ip:端口/`。

用`WinRAR`或者`7-zip`压缩全部文件至zip，用密码加密。用`ZIP legacy encryption`/`ZipCrypto`。名称为`main.76.jp.co.taito.groovecoasterzero.obb`.

覆盖`Android/obb/jp.co.taito.groovecoasterzero`里的`obb`文件。如文件夹不存在，需要手动创建。

打开游戏，观察私服的输出。

（提供的apk已经执行了如下的修改，可以忽略）

你可以通过修改apk里的obb校验函数然后修改`obb`里的`settings.cfg`来直连私服，无需中继软件。用顺手的`smali`反编译器来反编译`classes.dex`，然后去`jp.co.taito.groovecoasterzero/BootActivity`。删除`e()`里循环检查文件大小的部分。这部分会检查obb文件的大小，如果不一致会修改一个变量跳至`DownloadActivity`。我们想强制游戏读取。

### iOS

下载网盘里`install packages`里的`ipa`文件。

将`ipa`用压缩包软件打开。进`Payload`,`GROOVE 2`. 将`settings.cfg`提出。

文本编辑器打开`settings.cfg`，将`serverUrl`改成私服的`http://ip:端口/`。将`settings.cfg`拖回`ipa`。

侧载`ipa`即可。打开游戏，观察私服的输出。

</details>

## 管理员功能

数据库可以用DB Browser打开。

如果你想只对在白名单里的设备提供服务，开启`config.py`里的`AUTHORIZATION_NEEDED`，并将.php请求后面的设备ID加入`whitelist`列表。如果你想封禁设备或者Taito ID，将设备ID或者用户名加入`blacklist`列表。`reason`列可供你记录封禁原因。如果设备登陆该Taito ID，它将无法下载数据，不能登出，而且不能改名。如果设备在白名单开启后不在白名单里，或者设备被封禁，它将无法下载任何东西。

`getCrypt.py` 是一个用来单独解密`GET`请求后缀的脚本.

## 账号系统实装

账号仅用于保存/同步存档。Gcoin和歌曲所有权和设备绑定。不过，存档中已经解锁的曲目将在新的设备上可用。官方版不允许重命名及登出账号。私服则可以进行这些操作。不过，一个账号只能同时登陆一台设备，如果登录第二台设备，第一台设备将被挤掉。

## 排行榜系统实装

我推测官方服务器的行为取决于一个事实，即你不能注销你的账号，而且有一个最大设备数（5）。这意味着每个`账户`通过 `foreign key` 连接到 5 个`设备`，这样就可以统计所有拥有的 `权益`（`音乐`、`头像`等）和`游玩记录`。

在私服，用户可以任意注销设备。这意味着`权益`和`游玩记录`不可能保持一致，除非我们把`账户`当作`设备`，而这显然不是官服的行为。

目前的设置下，假如一台`设备`游玩时有关联`账户`，`账户`信息会同时保存，并且未来将持续显示当时连接的`账户`信息。`头像`信息随`游玩记录`保存，将不跟随`账户`或者`设备`。`Title`信息不在`游玩记录`里，也不在`账户`里，所以将和该设备的`Title`绑定。

## 排行榜数据

在停服前完成了一次较完整的数据抓取。每个难度的前`99950`位均被保留。数据和元数据可在这里下载。 [Google Drive](https://drive.google.com/file/d/1tsZnRnxPdUAoFPLfCzuXJFf9GgHR6rGz/view?usp=drive_link)

请注意，此数据仅用于分析，私服内置不会被实现。如果有需求，请Fork然后自行设计。

</details>

<details>
<summary>File Structure 文件结构</summary>
<br>

server/

├─ files/

│  ├─ gc2/

│  │  ├─ audio/ (found in android/ios.zip)

│  │  │  ├─ ogg and m4a zips

│  │  ├─ stage/ (found in android/ios.zip)

│  │  │  ├─ zip files for stage

│  │  ├─ model.pak (found in common.zip)

│  │  ├─ skin.pak (found in common.zip)

│  │  ├─ tunefile.pak (found in common.zip)

│  ├─ image/ (found in common.zip)

│  │  ├─ icon

│  │  ├─ title

│  ├─ web/ (found in common.zip)

│  │  ├─ webpage assets

├─ 7001.py (main script)

├─ getCrypt.py (debug purpose only)

├─ config.py (configuration script)

</details>


![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/stage_back10_big.png)
![](https://studio.code.org/v3/assets/BDOGr35iuNT4hc06y6O_ES5P96xr3SMqhQ2tdwI1KOY/test2.JPG)


## Journal

I've been forcing myself to document the process for personal project. So here goes.

<details>
<summary>English</summary>
<br>
Project Taiyo started on Feb. 19, 2024, as the effort to create a private server for Groove Coaster 2: Original Style. No prior effort was spent on the game, since the save file acquired from lp did unlock the majority of the track.

However, as updates slowed down and Groove Coaster 4max is scheduled to shut down, time were allocated to investigate the viability of a private server. Asset scraping was tedius as each song has multiple downloadable files, and there is no naming convention. Every zip file was acquired by hand(!) via manual downloading, which was soon proven unnecessary with the discovery of gcm-downloader.

The obb's decryption key was discovered in the android executable's lib file, and, during investigation of a config file within the obb, the server's address is directly editable. On the iOS, this config file is within the ipa. A proxy can be setup to mitm traffic for the same result. A simple server that handles asset delivery and static full-unlock profile was quickly developed.

An account system was developed that facilitates the save/load feature. The server request's GET field is encrypted, and, initially, the key and encryption method was not found. However, due to CBC encryption's flaw, part of the encrypted mess can still be used to identify users. Later, the key and IV to decrypt request was found in gcm-downloader, and used to implement a correct implementation of the server.

Besides the above features, all other functionality remains unimplemented. This was completed within a week (shorter than what is ideal, given project OverRide's priority). Some effort was spent on documenting the scraping, setup, and scripting, uploaded to a github repo, and the MVP is shelved.

In Janurary 2025, renewed effort was put on the project as Taito announced the cease of additional DLC, after a lackluster 2024 season. Groove Coin, a removed feature in-game, has been revived to facilitate a shop system. No longer is the server delivering static full-unlock save file, but the user can now acquire their own content in a balanced progression.

Additional effort was put on researching and REing various aspect of the game. 5 removed songs were re-enabled by lib editing, later via stage_param edit. Effort was spent on scripting a .pak unpacker and packer, which is successful and allow us to create own .pak files for delivery.

Effort was spent on the PC and Switch (waiwai) port, investigating the possiblilty of chart porting to Mobile. Switch version uses a significantly different system, charts lack critical elements and music is stored in header-removed opus. Porting from switch is deemed hard.

The PC version has exclusive songs/packs, and the chart/model files are an exact match from mobile asset. Music is in header-appended OGG, which is also compatible with Mobile. Porting is technically feasible if the format of stage_param can be RE'd.

On Jan. 24, 2025, Taito announced the end of service of the game. This prompted the creation of this repo and release of private server.

Effort was spent on porting charts from the arcade port (4max) to 2OS, and this process has been automated. The work and related tools has been added to the repo.

Additional avatars and skins were ported, but a 256 hard amount limit was encountered for avatar, after addressing a 200 soft limit.

Leaderboard ranking was scraped as a dataset just prior to the server shutdown and added to the repo.

Taito shutted down the server on March 31st, 2025, marking the completion of project Taiyo.

Overall, the project was a resounding success. The initial goal of creating a feature-rich private server was accomplished, with bonus points such as the toolchain, 4MAX expansion, and leaderboard dataset. If we were to nitpick, the save data hard limit was not addressed, various promotional material was not acquired from the server, and the leaderboard was not completely scraped.

</details>
