# 修改表情

> 使用的图片https://pan.quark.cn/s/d07357245728, 来自米游社的 枫达QAQ, 纥栖, 堇瓜团子, 1翎11

实际是使用自己的图片替换虾哥的图片文件, 小智使用的是lvgl的方式, 所以需要使用lvgl的图片格式转换

[免费在线图片改尺寸工具 - docsmall](https://docsmall.com/image-resize)

需要把图片压缩一下, 否则esp32存不下来以及会出现刷新卡的问题, 我这里使用的是64x64, 也提供了128x128的版本, 图片建议使用透明背景或者白色背景的

[Image Converter — LVGL](https://lvgl.io/tools/imageconverter)

压缩以后得图片按照原本的图片格式进行命名, 实际的文件名和情感是一一对应的

![image-20250310200420020](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503102004163.png)

## 问题

+ 没有对应的文件夹

答: 编译以后下载时候才有的文件

+ 改了以后还是原来的图片

看一下你的板子是32的还是64的表情, 我使用的是64的

![image-20250311123829935](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503111238593.png)

+ 表情的大小有限制

![image-20250313115333603](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503131153788.png)

+ 修改文字显示

![image-20250313115547253](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503131155323.png)

默认的长文本是换行, 可以使用滚动的方法减少显示空间

![image-20250313115638298](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503131156519.png)

替换成LV_LABEL_LONG_SCROLL_CIRCULAR