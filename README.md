# 「レンズモデル」
## プログラム概要
薄レンズによる光線の屈折を再現したレイトレーシングによるCGプログラムです。

OpenGLのフラグメントシェーダー内で各画素のレイトレーシングを計算することで、並行して各画素の計算を行っています。

10000フレーム描画するとプログラムを自動終了します。\
手動での終了時はコマンドラインからCtrl+Cで強制終了してください。

### 使用言語・ライブラリなど
使用言語：Python\
使用ライブラリ：numpy, OpenGL, glfw

### ギャラリー
<figure align="center">
  <img src=images/ray-4-16_focus-1000_focal-20_fnum-01.png width="80%">
  <figcaption>図1: ピント距離1000, 焦点距離20, F値0.1の画像</figcaption>
</figure>
<figure align="center">
  <img src=images/ray-4-16_focus-1100_focal-20_fnum-01.png width="80%">
  <figcaption>図2: ピント距離1100, 焦点距離20, F値0.1の画像
  </figcaption>
</figure>
ピント面が遠くなり、青い球のぼやけが少なくなっています。
<figure align="center">
  <img src=images/ray-4-16_focus-1000_focal-50_fnum-01.png width="80%">
  <figcaption>図3: ピント距離1000, 焦点距離50, F値0.1の画像
  </figcaption>
</figure>
焦点距離が長くなり、望遠レンズのように画角が狭くぼやけが強くなっています。
<figure align="center">
  <img src=images/ray-4-16_focus-1000_focal-20_fnum-10.png width="80%">
  <figcaption>図4: ピント距離1000, 焦点距離20, F値10の画像
  </figcaption>
</figure>
絞りが小さくなりぼやけが少なくなっています。

絞りを小さくすると本来は画像が暗くなりますが、このプログラムでは再現していません。

## ファイル構成
```text
lens
│  main.py              # メインプログラム
│  README.md            # 本ファイル
│
├─images                # スクリーンショット
│  ray-4-16_focus-1000_focal-20_fnum-01.png
│   └──  # ピント距離1000, 焦点距離20, F値0.1の画像
│  ray-4-16_focus-1100_focal-20_fnum-01.png
│   └──  # ピント距離1100, 焦点距離20, F値0.1の画像
│  ray-4-16_focus-1000_focal-50_fnum-01.png
│   └──  # ピント距離1000, 焦点距離50, F値0.1の画像
│  ray-4-16_focus-1000_focal-20_fnum-10.png
│   └──  # ピント距離1000, 焦点距離20, F値10の画像
│        
```

## 参考資料
薄レンズモデル（ThinLens model) - MochiMochi3D https://kinakomoti321.hatenablog.com/entry/2021/10/27/045649