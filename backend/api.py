from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Bu, henüz HTML'e bağlanmadı. Sadece bir metin döndürelim.
    return "Merhaba, Duygu Pusulası'na hoş geldin!"

if __name__ == '__main__':
    app.run(debug=True)