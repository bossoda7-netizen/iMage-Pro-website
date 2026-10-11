# iMage Pro 官网

免费、开源、本机创作的四语静态官网。首屏使用创作者提供的真实截图；滚动章节使用独立建模的界面与菜单。官网地址：https://bossoda7-netizen.github.io/iMage-Pro-website/ 。

应用源码：https://github.com/bossoda7-netizen/iMage-Pro 。网站通过 GitHub Pages 发布。

## 本地预览

在官网仓库根目录运行：

```sh
python3 -m http.server 8126 --bind 127.0.0.1 --directory public
```

打开 http://127.0.0.1:8126/ 。3D 模型需要 HTTP 环境。

## 文件组织

- `public/`：实际发布的网站。含四语首页、隐私说明、活动规则、第三方许可、网站样式与脚本。
- `public/assets/product/`：四语 × 深浅外观的8张 WebP 首图，保留完整透明范围及原始阴影。
- `public/assets/3d/`：8个语言／外观 GLB 与48张手机及减少动态效果回退图。
- `public/assets/brand/`、`icons/`、`social/`：页面需要的图标、favicon 与分享封面。
- `public/assets/downloads/release.json`：版本、系统要求及真实发布链接配置。
- `public/assets/legal/`、`public/vendor/`：必要许可证及本地 GSAP、Three.js 依赖。
- `models/image-pro.blend`：唯一基础可编辑场景，用于生成四语模型，不属于网站发布目录。
- `content/`：翻译、模型目录、来源与尺寸记录、验收清单。
- `scripts/`：当前生成、检查与打包流程。

素材验收页、旧截图、重复模型、未使用视频和插画、旧制作脚本已移到项目外 `../iMage Pro 官网筹备/制作备份/官网清理-2026-10-10/`（相对于应用项目）。没有修改用户原始素材。

## 生成与检查

```sh
python3 scripts/build-site.py
python3 scripts/finalize-kit.py
python3 scripts/package-kit.py
```

后两项需使用带 Pillow 的 Python 环境。导入新首图：`scripts/import-hero.py <素材文件夹>`，目录内使用 `中文白.png`、`中文黑.png` 等四语命名。

模型制作：模型重建需要在相邻目录克隆应用源码为 `iMage-Pro`（用于字体），或通过 `IMAGEPRO_FONT_PATH` 指定已获许可的字体文件。先用 Blender 后台执行 `scripts/build-blender.py`，再执行 `scripts/build-localized-models.py`。本地化流程生成8个 GLB 和48张海报；中间深浅场景写入临时目录后清理，不进入公开目录。渲染后运行 `scripts/optimize-posters.py`，将海报无损转换为 WebP 并逐像素校验，原始 PNG 留在项目外。`render-dark-posters.py` 由本地化流程调用。

官网基于 Three.js 与 GSAP ScrollTrigger。首次进入3D章节仅请求当前语言与外观模型；切换系统外观时才加载另一套，之后复用。手机与减少动态效果设置使用同语言／外观的静态图，不下载 GLB。

## 已确认的材质

浅色玻璃菜单透射0.995，工具栏与切换器0.998；粗糙度分别0.52、0.38，边缘0.065。宽倒角采用12段连续弧面；深色圆角与倒角收紧，采用8段弧面。文字和控件单独绘制，避免玻璃折射使文字模糊。减少透明度或增强对比度偏好使用实色回退。该效果为网页物理材质模拟。

## 发布

GitHub Pages 只发布 `public/`。可编辑场景、制作记录与项目外私人筹备文件不部署。源码与素材压缩包生成到项目外筹备目录。

`release.json` 配置真实下载和源码地址；只有确认 Release 附件可下载才启用 `releaseReady`。`notarized` 独立记录 Apple 公证状态，预览版为 `false`，页面保留安装说明。正式站点已配置 canonical URL 与绝对 HTTPS 分享图地址。确认月度灵感展的主题、日期和维护安排后再开放投稿。保留随包第三方许可证。

网站没有分析 SDK、远程字体或自动投稿后台。隐私政策中的运营安排需要按实际实施维护。
