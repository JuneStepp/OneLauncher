# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'PyLotRO/pylotro'],
             pathex=['C:\\pyinstaller'])
pyz = PYZ(a.pure, level=9)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\pylotro', 'pylotro.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='PyLotRO\\PyLotRO_Menu.ico')
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='dist', icon='PyLotRO\\PyLotRO_Menu.ico')
