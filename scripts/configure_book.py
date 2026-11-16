"""Regenerate navigation and the lesson table; preserve authored coverage notes."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
lessons = json.loads((ROOT / "content/lessons.json").read_text())
groups = [(0,5,"Understand and access"),(5,13,"Analyze and question"),(13,19,"Map and communicate"),(19,22,"Reproduce and decide"),(22,28,"Connect to DestinE workflows"),(28,len(lessons),"Explore Earth-system components")]
lines = ['version: 1', 'project:', '  id: destine-learning-lab', '  title: Destination Earth Learning Lab', '  description: An independent book with original synthetic experiments', '  github: https://github.com/jltobias/JupyterLite-Destination-Earth-Digital-Twin', '  bibliography:', '    - book/references.bib', '  toc:', '    - file: book/index.md', '    - file: book/coverage.md', '    - file: book/official-access.md']
for start,end,title in groups:
    lines += [f'    - title: {title}', '      children:']
    lines += [f'        - file: content/{item["slug"]}.ipynb' for item in lessons[start:end]]
lines += ['site:', '  template: book-theme', '  title: Earth / Lab', '  options:', '    logo_text: Earth / Lab']
(ROOT / "myst.yml").write_text('\n'.join(lines)+'\n', encoding="utf-8")
coverage = ['---','title: Coverage and learning paths','---','', 'These canonical notebooks serve both book and Lab. All default exercises are original and synthetic; official connections and production models remain outside the browser implementation.', '', '| Notebook | Runnable learning goal |', '|---|---|']
for item in lessons:
    coverage.append(f'| [{item["title"]}](../content/{item["slug"]}.ipynb) | {item["objectives"]} |')
notes = (ROOT / "book/coverage.md").read_text(encoding="utf-8").partition("\n## Capability boundaries\n")[2]
if not notes.strip():
    raise ValueError("Coverage notes are missing; refusing to replace the authored component boundaries")
coverage += ["", "## Capability boundaries", notes.rstrip()]
(ROOT / "book/coverage.md").write_text('\n'.join(coverage)+'\n', encoding="utf-8")
