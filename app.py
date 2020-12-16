import os
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from logging import DEBUG, ERROR, basicConfig, getLogger


#########################
# CONFIGURATION SECTION #
#########################

# --- directory configuration
path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')
LOG_FOLDER = os.path.join(path, 'logging')
LOG_FILE = 'logfile.log'
LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

if not os.path.isdir(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)

# --- logger configuration (levels: debug, info, warning, error, critical)
basicConfig(filename=os.path.join(LOG_FOLDER, LOG_FILE),
            level=DEBUG,
            format=LOG_FORMAT,
            filemode='w')
logger = getLogger(__name__)

# --- app configuration and setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'p@\x90\xb4\nO\xa2\x18\x10\x0eB\x88\xd0\xa8\xf5o\xfaC\x898n\x99\xf0['
app.config['MAX_CONTENT_PATH'] = '~'

# note: to generate the SECRET_KEY, one way is to
#    >>> import os
#    >>> os.urandom(24) # 24 random bytes


# --- temporary store
stored_files = []


# --- helper functions
def store_file(file):
    stored_files.append(dict(
        file_name=file,
        client_name="test_client",
        date_created=datetime.utcnow()
    ))


def recent_uploads(num):
    return sorted(stored_files, key=lambda up: up['date_created'], reverse=True)[:num]


def is_allowed(file):
    return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Model classes
class Customer:
    def __init__(self, customer_name, registered_email):
        self.customer_name = customer_name
        self.registered_email = registered_email


# --- View functions
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title="file uploader",
                           testo="Please use this page to upload your data.",
                           recent_uploads=recent_uploads(4))


@app.route('/upload')
def upload():
    return render_template('upload.html', title="upload", testo="Please enter the file containing the raw data. "
                                                                "Allowed Types are: `csv`, `xlsx`",
                           customer=Customer("Esteve", "esteve@infinity.com"))


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        flash(f"Stored file: `{f.filename}`")
        logger.debug(f"stored file `{f.filename}`")
        store_file(f.filename)
        return redirect(url_for('index'))


# --- Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# --- main
if __name__ == '__main__':
    app.run(debug=True)