

from PyInstaller.utils.hooks import collect_data_files

# Collect matplotlib data
datas = collect_data_files('matplotlib')

# Include your sample CSV inside the EXE bundle
datas.append((
    r"C:\Users\vignesh\OneDrive\Desktop\ChemicalVisualizer\desktop-app\sample_equipment_data.csv",
    "sample"
))

block_cipher = None

a = Analysis(
    ['desktop_app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ChemicalVisualizerDesktop',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=None
)
