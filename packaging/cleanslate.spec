import ast
import json
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).parent
tree = ast.parse((root / "cleanslate/core/osint.py").read_text())
modules = next(ast.literal_eval(n.value) for n in tree.body
               if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "HOLEHE_MODULES" for t in n.targets))
hidden = ["holehe.modules." + name for name in modules]
hidden += collect_submodules("uvicorn") + ["webview.platforms.cocoa", "keyring.backends.macOS"]
a = Analysis([str(root / "packaging/macos_entry.py")], pathex=[str(root)],
             binaries=[], datas=[(str(root / "cleanslate/web/static"), "cleanslate/web/static"),
                                (str(root / "build/legal"), "legal")],
             hiddenimports=hidden, excludes=["pytest", "_pytest", "tkinter", "IPython", "PIL"],
             noarchive=False)
(root / "build/analysis.json").write_text(json.dumps({"modules": [name for name, _, _ in a.pure],
    "binaries": [{"name": name, "source": source} for name, source, _ in a.binaries]}, indent=2))
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CleanSlate", console=False,
          target_arch="arm64", codesign_identity=None)
coll = COLLECT(exe, a.binaries, a.datas, name="CleanSlate")
app = BUNDLE(coll, name="CleanSlate.app", icon=str(root / "CleanSlate.app/Contents/Resources/AppIcon.icns"),
             bundle_identifier="com.pietromey.cleanslate", version="1.0.0",
             info_plist={"CFBundleName": "CleanSlate", "CFBundleDisplayName": "CleanSlate",
                         "CFBundleVersion": "1", "LSMinimumSystemVersion": "26.0",
                         "NSHighResolutionCapable": True})
