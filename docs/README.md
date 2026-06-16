# 文档目录

技术方法清单：[`TOOLS_USAGE.md`](TOOLS_USAGE.md)（本作品实际采用的可视化方法与工具）

**零基础解读**（答辩 / 读 Word / 录屏）：[`submission/NyxViz_零基础完全解读.md`](submission/NyxViz_零基础完全解读.md)

| 目录 | 内容 | 命令 |
|------|------|------|
| [`submission/`](submission/) | **提交物**（作品说明 docx、官方答卷、代表图、清单） | `npm run submission-pack` |
| [`report/`](report/) | 四题 **Markdown 正文**（单一文字源） | `npm run export-report` |
| [`figures/`](figures/) | 全部 **PNG / GIF** 配图 | `npm run figures` |
| [`competition/`](competition/) | 任务清单、**TTS 旁白**（`VIDEO_NARRATION_TTS.txt`）、分镜/录屏手册 | — |
| [`showcase/`](showcase/) | 单文件离线 HTML（本地生成，不入库） | `npm run showcase` |

**整理 Word 时**：打开 `submission/NyxViz_作品说明文档.docx`；正文扩写改 [`tools/python/work_doc_content.py`](../tools/python/work_doc_content.py) → 重跑 `npm run export-docx` 或 `submission-pack`。四题简答仍走 `report/*.md` + 官方答卷。
