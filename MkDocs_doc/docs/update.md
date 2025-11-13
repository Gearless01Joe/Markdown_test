当你在本地更新了文档（例如新增 `about.md` 或修改 `.md`、`mkdocs.yml`），按照下面流程就能同步到 GitHub Pages。建议顺序执行，每步都确认完成。

## 1. 本地预览（可选）
```powershell
cd MkDocs_doc
mkdocs serve
```
在浏览器打开 `http://127.0.0.1:8000/`，确认文档显示正常。调试完按 `Ctrl+C` 停止服务。

## 2. 构建一次并确保成功
```powershell
mkdocs build
```
要求没有致命错误，`docs/` 中新增的文件（如 `about.md`）都写进 `mkdocs.yml` 的 `nav`，以免出现遗漏警告。

## 3. 提交代码（`test` 分支）
```powershell
cd ..
git add .
git commit -m "Add about page"
git push markdown test
```
回到仓库根目录（cd ..），保持代码版本库和文档源同步。

## 4. 部署到 GitHub Pages
确认仍在虚拟环境里：
```powershell
cd MkDocs_doc
mkdocs gh-deploy --clean --remote-name markdown
```
看到 “Copying … to ‘gh-pages’ branch and pushing to GitHub.” 且没有报错，说明发布成功。

注意：如果出现了
```powershell
Failed to connect to github.com
```
执行：git push markdown test，可以成功连接的时候，再执行部署的命令。

## 5. GitHub 页面的更新
保持 GitHub 仓库 Pages 设置（Branch: `gh-pages` / root）不动。几分钟后访问 `https://gearless01joe.github.io/Markdown_test/`，新页面就会出现。若浏览器缓存导致旧内容未刷新，可以 `Ctrl+F5` 或换浏览器试一下。

只要按照这五步（**预览 → 构建 → 提交 → 部署 → 检查**）就能把未来的文档更新自动发布到线上的 GitHub Pages 站点。