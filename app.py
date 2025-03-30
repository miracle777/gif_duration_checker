import os
from flask import Flask, request, render_template, flash, redirect, url_for
from PIL import Image, UnidentifiedImageError
import io # Pillow 9.1.0以降で推奨される io モジュール

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' # セッション管理のための秘密鍵 (適当な文字列でOK)

# アップロードされるファイルの拡張子を制限 (GIFのみ)
ALLOWED_EXTENSIONS = {'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # ファイルがリクエストに含まれているかチェック
        if 'gif_file' not in request.files:
            flash('ファイルが選択されていません')
            return redirect(request.url)

        file = request.files['gif_file']

        # ファイル名が空でないかチェック
        if file.filename == '':
            flash('ファイルが選択されていません')
            return redirect(request.url)

        # ファイルが選択され、拡張子が許可されているかチェック
        if file and allowed_file(file.filename):
            try:
                # Pillowで画像を開く (ファイルストリームから直接読み込む)
                img = Image.open(file.stream)

                # GIF形式であることを確認 (Pillowが読み込めた時点で形式はある程度保証されるが念のため)
                if img.format != 'GIF':
                     flash('GIFファイルを選択してください。')
                     return redirect(request.url)

                total_duration = 0
                frame_count = 0
                # フレームごとに処理
                try:
                    while True:
                        # 各フレームの表示時間を取得 (ミリ秒単位, 'duration'キーがない場合や0の場合は100ms(0.1秒)を仮定することが多い)
                        # ここではキーが存在しない場合は0として加算しないか、デフォルト値(例: 100ms)にするか選べます
                        duration = img.info.get('duration', 0)
                        # 一般的なブラウザの挙動に合わせ、0msの場合は100msとして扱う場合
                        # if duration == 0:
                        #     duration = 100
                        total_duration += duration
                        frame_count += 1
                        # 次のフレームへ (ファイルの終端でEOFError)
                        img.seek(img.tell() + 1)
                except EOFError:
                    pass  # ファイルの終端に到達

                if frame_count == 0:
                     flash('GIFファイルからフレーム情報を読み取れませんでした。')
                     return redirect(request.url)

                # ミリ秒を秒に変換
                total_duration_sec = total_duration / 1000.0

                # 結果をテンプレートに渡して表示
                return render_template('index.html',
                                       filename=file.filename,
                                       duration=f"{total_duration_sec:.3f}", # 小数点以下3桁まで表示
                                       frame_count=frame_count)

            except UnidentifiedImageError:
                flash('有効な画像ファイルではありません。GIFファイルを選択してください。')
                return redirect(request.url)
            except Exception as e:
                flash(f'処理中にエラーが発生しました: {e}')
                return redirect(request.url)

        else:
            flash('許可されていないファイル形式です。GIFファイルを選択してください。')
            return redirect(request.url)

    # GETリクエストの場合は、アップロードフォームを表示
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) # debug=True は開発時のみ。本番運用ではFalseにする