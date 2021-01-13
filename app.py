import os
from datetime import datetime

from flask import Flask, render_template, flash, redirect, url_for, request

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from logging import DEBUG, basicConfig, getLogger

from flask_wtf import Form
from wtforms import FileField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, Email, ValidationError, EqualTo

from flask_login import LoginManager, login_required, UserMixin, login_user, current_user, logout_user

from google.cloud import storage


#########################
# CONFIGURATION SECTION #
#########################

# --- app configuration and setup
# constant setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
LOG_DIR = os.path.join(BASE_DIR, 'logging')
LOG_FILE = 'logfile.log'
LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xls', 'xlsx'}
DB_NAME = 'bitbed.db'

# dir structure setup
if not os.path.isdir(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

# logger option setup (levels: debug, info, warning, error, critical)
basicConfig(filename=os.path.join(LOG_DIR, LOG_FILE),
            level=DEBUG,
            format=LOG_FORMAT,
            filemode='w')
logger = getLogger(__name__)

# --- app init
app = Flask(__name__)

# --- app options
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['SECRET_KEY'] = 'p@\x90\xb4\nO\xa2\x18\x10\x0eB\x88\xd0\xa8\xf5o\xfaC\x898n\x99\xf0['
app.config['MAX_CONTENT_PATH'] = BASE_DIR

# --- database setup
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, DB_NAME)}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db connection setup
db = SQLAlchemy(app)

# --- authentication setup
login_manager = LoginManager()
# authentication options
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
# initialize login manager
login_manager.init_app(app)

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


# --- helper functions
# Fake login -- TODO: REMOVE THIS
# def logged_in_customer():
#     return Customer.query.filter_by(c_name="pizza").first()


@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(int(user_id))


def upload_to_blob(filename):
    client = storage.Client.from_service_account_json(json_credentials_path='bosch-dashboard-295910-b9306f4b5581.json')
    bucket = client.get_bucket('file-uploader_vol')
    blob = bucket.blob(filename)
    blob.upload_from_filename(os.path.join(UPLOAD_DIR, secure_filename(filename)))


def initdb():
    db.create_all()
    db.session.add(Customer(c_name="init", c_email="init@init.it", password='test'))
    db.session.commit()
    print("INITIALIZED THE DATABASE")


def dropdb():
    db.drop_all()
    print("DROPPED DATABASE")


def is_allowed(file):
    return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- ## FORMS ## WTF Forms implementation ==> TODO: refactor to a separate module
class LoginForm(Form):
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class SignupForm(Form):
    username = StringField('Username',
                           validators=[DataRequired(), Length(3, 80),
                                       Regexp('^[A-Za-z0-9_]{3,}$',
                                              message='Usernames consist of numbers, letters, and underscores.')])
    password = PasswordField('Password',
                             validators=[DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    email = StringField('Email',
                        validators=[DataRequired(), Length(1, 120), Email()])

    def validate_email(self, email_field):
        if Customer.query.filter_by(c_email=email_field.data).first():
            raise ValidationError('There already is a user with this email address')

    def validate_username(self, username_field):
        if Customer.query.filter_by(c_name=username_field.data).first():
            raise ValidationError('This username is already taken.')


class UploadForm(Form):
    file_name = FileField('file_name', validators=[DataRequired()])
    file_description = StringField('file_description')

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
            flash(f'Allowed file types: {ALLOWED_EXTENSIONS}')
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


class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(80), unique=True)
    c_email = db.Column(db.String(120), unique=True)
    c_files = db.relationship('File', backref='customer', lazy='dynamic')
    # backref argument: means that on the other side of the relation, which is on the File side, there will be a
    # property called `customer`, which will hold the user objects, so we'll not have to work with the customer.id field
    # on the File class. Instead we can work with real Python objects since there will be a list of `file`
    # objects on every `customer`, and there will be a `customer` object on every `file`. That way we hide the mechanics
    # of setting up foreign keys on the database.
    password_hash = db.Column(db.String)

    @property
    def password(self):
        raise AttributeError('password: write-only field')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        return Customer.query.filter_by(c_name=username).first()

    def __repr__(self):
        return f"<Customer {self.c_name} {self.c_email}>"


# --- VIEWS: View functions
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           testo="This is Bedrock File Uploader.",
                           recent_uploads=File.recent_uploads(4))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file_name = form.file_name.data
        file_description = form.file_description.data
        file_name.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_name.filename)))

        fm = File(customer=current_user, f_name=file_name.filename, f_description=file_description)
        logger.debug(f"fm {fm} {current_user} - {file_name.filename} - {file_description}")

        db.session.add(fm)
        db.session.commit()
        upload_to_blob(file_name.filename)
        flash(f"Stored file: `{file_name.filename}`")
        logger.debug(f"stored file `{file_name.filename}`")

        return redirect(url_for('index'))
    return render_template("upload.html", testo="Please use this page to upload your data.", cust=current_user,  form=form)


@app.route('/customer/<customer_name>')
@login_required
def customer(customer_name):
    cust = Customer.query.filter_by(c_name=current_user.c_name).first_or_404()
    logger.debug(f"==> {cust} --- {cust.c_name}")
    return render_template('customer.html', cust=cust)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user = Customer.get_by_username(form.username.data)
    if user is not None and user.check_password(form.password.data):
        login_user(user, form.remember_me.data)
        flash(f"Logged in as {user.c_name}")

        return redirect(request.args.get('next') or url_for('customer', customer_name=user.c_name))
    else:
        flash("Incorrect username or password.")
    return render_template("login.html", form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        cust = Customer(c_email=form.email.data,
                        c_name=form.username.data,
                        password=form.password.data)
        db.session.add(cust)
        db.session.commit()
        flash(f'Welcome, {cust.c_name}! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html', testo="Please use this page to Sign up.", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# --- Error handling
@app.errorhandler(404)
def page_not_found():
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error():
    return render_template('500.html'), 500


# --- main
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
