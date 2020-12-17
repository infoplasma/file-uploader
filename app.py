import os
from datetime import datetime
from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from logging import DEBUG, basicConfig, getLogger
from flask_wtf import Form
from wtforms import FileField, StringField
from wtforms.validators import DataRequired


#########################
# CONFIGURATION SECTION #
#########################

# --- directory configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
LOG_DIR = os.path.join(BASE_DIR, 'logging')
LOG_FILE = 'logfile.log'
LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}
DB_NAME = 'bitbed.db'

if not os.path.isdir(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

# --- logger configuration (levels: debug, info, warning, error, critical)
basicConfig(filename=os.path.join(LOG_DIR, LOG_FILE),
            level=DEBUG,
            format=LOG_FORMAT,
            filemode='w')
logger = getLogger(__name__)

# --- app configuration and setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['SECRET_KEY'] = 'p@\x90\xb4\nO\xa2\x18\x10\x0eB\x88\xd0\xa8\xf5o\xfaC\x898n\x99\xf0['
app.config['MAX_CONTENT_PATH'] = BASE_DIR
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, DB_NAME)}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# notes:
#  1. to generate the SECRET_KEY, one way is to
#    >>> import os
#    >>> os.urandom(24) # 24 random bytes
#
# 2. to suppress warning:
# >>> C:\Users\Lorenzo
# Amante\Documents\PROJECTS\PYTHON\venvs\file-uploader\lib\site-packages\flask_sqlalchemy\__init__.py:834:
# FSADeprecationWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in
# the future.  Set it to True or False to suppress this warning. 'SQLALCHEMY_TRACK_MODIFICATIONS adds significant
# overhead and '
#   must set: >>> app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False either True or False.

# --- create db connection
db = SQLAlchemy(app)

# --- temporary store
stored_files = []


# --- helper functions

# Fake login
def logged_in_customer():
    return Customer.query.filter_by(c_name="pippo").first()


""" no longer in use
def store_file(file, desc):
    stored_files.append(dict(
        file_name=file,
        client_name="test_client",
        file_description=desc,
        date_created=datetime.utcnow()
    ))
"""

""" REPLACING THIS WITH staticmethod within the File model
def recent_uploads(num):
    return sorted(stored_files, key=lambda up: up['date_created'], reverse=True)[:num]
"""


def initdb():
    db.create_all()
    db.session.add(Customer(c_name="pippo", c_email="pippo@piscopauro.com"))
    db.session.add(Customer(c_name="pizza", c_email="pizza@ngrillo.com"))
    db.session.commit()
    print("INITIALIZED THE DATABASE")


def dropdb():
    db.drop_all()
    print("DROPPED DATABASE")


def is_allowed(file):
    return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- FORMS: WTF Forms implementation ==> TODO: refactor to a separate module
class IndexForm(Form):
    title = "File Uploader"


class CustomerForm(Form):
    title = "Customer data"


class UploadForm(Form):
    file_name = FileField('file_name', validators=[DataRequired()])
    file_description = StringField('file_description')
    customer_name = "Esteve"
    registered_email = "esteve@infinity.com"
    title = "upload"

    def validate(self):
        logger.debug(msg=self.file_name.data.filename)
        logger.debug(msg=self.file_description.data)
        if not Form.validate(self):
            return False
        if not self.file_description:
            self.file_description = self.file_name.data.filename
        if is_allowed(self.file_name.data.filename):
            return True
        else:
            flash('Allowed file types: txt, pdf, png, jpg, jpeg, gif')
            return False


# --- MODELS: SQLAlchemy Model classes (Model ==> SQL Table) ==> TODO: refactor to a separate module
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(120), nullable=False)
    f_description = db.Column(db.String(250), nullable=True)
    f_date_added = db.Column(db.DateTime, default=datetime.utcnow)    # NOTE: do not pass `()` to utcnow, as otherwise
    # it will resolve to the date at the time o construction? 
    # This way the date will be generated each time we create a new one
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    @staticmethod
    def recent_uploads(num):
        return File.query.order_by(desc(File.f_date_added)).limit(num)  # select * from `file` order by `f_date_added` desc limit num

    def __repr__(self):
        return f"<File {self.f_name} {self.f_description}>"


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(80), unique=True)
    c_email = db.Column(db.String(120), unique=True)
    c_files = db.relationship('File', backref='customer', lazy='dynamic')

    # backref argument: means that on the other side of the relation, which is on the File side, there will be a
    # property called `customer`, which will hold the user objects, so we'll not have to work with the customer.id field
    # on the File class. Instead we can work with real Python objects since there will be a list of `file`
    # objects on every `customer`, and there will be a `customer` object on every `file`. That way we hide the mechanics
    # of setting up foreign keys on the database.

    def __repr__(self):
        return f"<Customer {self.c_name}: {self.c_email}>"


# --- VIEWS: View functions
@app.route('/')
@app.route('/index')
def index():
    form = IndexForm()
    return render_template('index.html',
                           title="file uploader",
                           testo="Please use this page to upload your data.",
                           recent_uploads=File.recent_uploads(4),
                           form=form)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file_name = form.file_name.data
        file_description = form.file_description.data
        file_name.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_name.filename)))

        fm = File(customer=logged_in_customer(), f_name=file_name.filename, f_description=file_description)
        logger.debug(f"fm {fm} {logged_in_customer()} - {file_name.filename} - {file_description}")

        db.session.add(fm)
        db.session.commit()

        flash(f"Stored file: `{file_name.filename}`")
        logger.debug(f"stored file `{file_name.filename}`")

        return redirect(url_for('index'))
    return render_template("upload.html", form=form)


@app.route('/customer/<customer_name>')
def customer(customer_name):
    form = CustomerForm()
    cust = Customer.query.filter_by(c_name=customer_name).first_or_404()
    logger.debug(f"==> {cust} --- {customer_name}")
    return render_template('customer.html',
                           cust=cust,
                           form=form)


""" BEFORE CHANGING TO WTF FORM NEW VIEW ==>
def upload():

    return render_template('upload.html', title="upload", testo="Please enter the file containing the raw data. "
                                                                "Allowed Types are: `csv`, `xlsx`",
                           customer=Customer("Esteve", "esteve@infinity.com"))
"""

""" no longer in use
@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        file_name = form.file_name.data
        file_description = form.file_description.data
        file_name.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_name.filename)))
        flash(f"Stored file: `{file_name.filename}`")
        logger.debug(f"stored file `{file_name.filename}`")
        store_file(file_name.filename, file_description)
        return redirect(url_for('index'))
    return render_template(url_for('upload'))
"""

""" BEFORE CHANGING TO WTF FORM NEW VIEW ==>
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        file_description = request.form['file_description']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        flash(f"Stored file: `{f.filename}`")
        logger.debug(f"stored file `{f.filename}`")
        store_file(f.filename, file_description)
        return redirect(url_for('index'))
    return render_template(url_for('upload'))
"""


# --- Error handling
@app.errorhandler(404)
def page_not_found():
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error():
    return render_template('500.html'), 500


# --- main
if __name__ == '__main__':
    app.run(debug=True)
