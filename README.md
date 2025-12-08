# tips_client
这是 tips 应用的前端，tips 应用采用了fastapi + MySql 作为后端，使用Requests库与后端进行通信。

前端基于命令行界面，使用Rich库进行美化

## 安装步骤
1. 克隆代码库到本地


2. 进入代码目录
``` bash
cd tips_client
```
3. 运行安装脚本
``` bash
chmod +x install.sh
./install.sh
```

##  使用方法
现在tips就集成到你的系统中了，可以使用 `tips` 命令来启动它。
在使用之前，你需要先注册一个账号，可以使用 `tips --signup` 命令来注册。
注册成功后，你就可以使用 `tips` 命令来启动客户端，登录后即可使用各种功能。
