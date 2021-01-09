![sniffselect](https://user-images.githubusercontent.com/2152766/104090255-8159f000-526d-11eb-87ee-f46fbe261326.gif)

### Maya Sniffer

<img src=https://img.shields.io/badge/Maya-2015--2020-green> <img src=https://img.shields.io/badge/Python%20API-2.7%20%7C%203.9-steelblue>

Ever wondered which nodes are responsible for that 600 mb+ Maya scene file?

Use [Treemapping](https://en.wikipedia.org/wiki/Treemapping) visualisation to find the most bloated nodes in the current scene or scene on disk.

**Features**

- Fast, resizable UI
- Parsing at 50 mb/sec
- Dependency-free, single-file install
- Script Editor support
- Terminal support
- Percentage of total size per node
- Color-coded node types
- Click to copy node name to clipboard
- Click to select node in Maya
- Tooltip with full node name

**Roadmap**

- [ ] **Group by hierarchy** SpaceSniffer has the ability to "zoom out" by grouping hierarchies under one large box. That would help snuff out those huge groups with thousands of offset groups and metadata stored as strings.
- [ ] **More metadata** Hovering takes a while since it's a tooltip. Would be good having not only a faster and more visible popup, but also the full path (rather than just the name) along with parent, number of children, number of attributes, number of connections etc. To help make the decision to kill easier
- [ ] **Click to kill** Modify the file directly, by removing any offending nodes you know aren't used or necessary.
- [ ] **Visualise plug-ins** Spot and kill viruses like Turtle on-sight, with one click

Pull-requests are welcome.

<br>

### Install

It's a single file, no dependencies.

1. Download [`maya_sniffer.py`](https://raw.githubusercontent.com/mottosso/maya-sniffer/master/maya_sniffer.py)
2. Store in `~/maya/scripts`, e.g. `c:\Users\marcus\Documents\maya\scripts`
3. See [Usage](#usage) below

<br>

### Usage

From the Script Editor.

```py
import maya_sniffer
maya_sniffer.show()
```

From a terminal.

```bash
python maya_sniffer.py c:\path\to\scene.ma
```

Here's the currently coloured node types.

| Color | Node Type
|:------|:-----
| <img width=25 src="https://swatch.now.sh/?color=%2375BCE1"> | `transform`
| <img width=25 src="https://swatch.now.sh/?color=%23EDD377"> | `nurbsCurve`
| <img width=25 src="https://swatch.now.sh/?color=%23C0935E"> | `mesh`
| <img width=25 src="https://swatch.now.sh/?color=%2391DC73"> | `joint`
| <img width=25 src="https://swatch.now.sh/?color=%23DD6A6A"> | `camera`
| <img width=25 src="https://swatch.now.sh/?color=%23E17839"> | `skinCluster`
| <img width=25 src="https://swatch.now.sh/?color=%23E14530"> | `dagPose`
| <img width=25 src="https://swatch.now.sh/?color=%23D474EC"> | `animCurve`

<br>

### Why?

Whenever I run out of diskspace, I use a free Windows utility called [SpaceSniffer](http://www.uderzo.it/main_products/space_sniffer/). 2 minutes later, I've got the space I was looking for along with a greater understanding of where space typically ends up.

I wanted something like this for Maya.

<br>

### How it works

Maya Sniffer counts the number of ASCII characters used when saving each node to disk.

That's it.

It's real silly and doesn't tell you how complex or heavy your scene is at run-time. Instead, it'll give you an approximation of where size is and how to recover it.

<br>

### Showcase

**Resizable UI**

![maya_sniffer](https://user-images.githubusercontent.com/2152766/104033410-659c0e80-51c7-11eb-8ac7-695e3c77e7ac.gif)

**Script Editor**

![image](https://user-images.githubusercontent.com/2152766/104031988-6469e200-51c5-11eb-904c-a2593a757f70.png)

**Standalone**

> Requires Python 2/3 and PySide2

![image](https://user-images.githubusercontent.com/2152766/104016452-4775e480-51ae-11eb-997f-1e9bb9fdd5e5.png)
