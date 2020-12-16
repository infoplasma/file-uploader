from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'p@\x90\xb4\nO\xa2\x18\x10\x0eB\x88\xd0\xa8\xf5o\xfaC\x898n\x99\xf0['

class Customer:
    def __init__(self, customer_name, registered_email):
        self.customer_name = customer_name
        self.registered_email = registered_email


app.config['UPLOAD_FOLDER'] = '~'
app.config['MAX_CONTENT_PATH'] = '~'


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title="BEDROCK FILE UPLOAD", testo="Please use this page to upload your data.")


@app.route('/upload')
def upload():
    return render_template('upload.html', title="UPLOAD PAGE", customer=Customer("Esteve", "esteve@infinity.com"))


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        flash(f"Stored file: `{f.filename}`")
        return 'file uploaded successfully'
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)