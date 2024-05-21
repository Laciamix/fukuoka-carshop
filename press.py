from flask import Flask, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms import FileField, SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired
import os
import subprocess
from werkzeug.utils import secure_filename
from pathlib import Path
from jinja2 import Environment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_id(self):
        return self.username

# Simulated user database
users = {'admin': User('admin', 'godbless1180')}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

def pathlib_path_parent(file_path):
    return str(Path(file_path).parent)

app.jinja_env.filters['pathlib_path_parent'] = pathlib_path_parent

# Base directory
BASE_DIR = './'

# Ensure the base directory exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

class CommandForm(FlaskForm):
    command = StringField('Command', validators=[DataRequired()])
    submit = SubmitField('Run')

class UploadForm(FlaskForm):
    file = FileField('Upload File', validators=[DataRequired()])
    submit = SubmitField('Upload')

class CreateFolderForm(FlaskForm):
    folder_name = StringField('Folder Name', validators=[DataRequired()])
    submit = SubmitField('Create Folder')

class EditFileForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save')

class RenameFileForm(FlaskForm):
    new_name = StringField('New Name', validators=[DataRequired()])
    submit = SubmitField('Rename')

def get_files_and_folders(directory):
    items = []
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            items.append({'name': item, 'type': 'folder'})
        else:
            items.append({'name': item, 'type': 'file'})
    return items

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/dashboard/<path:path>', methods=['GET', 'POST'])
def dashboard(path):
    current_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(current_path):
        flash('Path does not exist.', 'danger')
        return redirect(url_for('dashboard'))

    upload_form = UploadForm()
    folder_form = CreateFolderForm()

    if upload_form.validate_on_submit():
        file = upload_form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_path, filename))
        flash('File uploaded successfully!', 'success')
        return redirect(url_for('dashboard', path=path))

    if folder_form.validate_on_submit():
        folder_name = secure_filename(folder_form.folder_name.data)
        os.makedirs(os.path.join(current_path, folder_name))
        flash('Folder created successfully!', 'success')
        return redirect(url_for('dashboard', path=path))

    items = get_files_and_folders(current_path)
    return render_template('dashboard.html', upload_form=upload_form, folder_form=folder_form, items=items, current_path=path)

@app.route('/delete/<path:path>')
def delete_item(path):
    item_path = os.path.join(BASE_DIR, path)
    if os.path.exists(item_path):
        if os.path.isdir(item_path):
            os.rmdir(item_path)
        else:
            os.remove(item_path)
        flash('Item deleted successfully!', 'success')
    else:
        flash('Item not found', 'danger')
    return redirect(url_for('dashboard', path=os.path.dirname(path)))

@app.route('/edit/<path:path>', methods=['GET', 'POST'])
def edit_file(path):
    file_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        flash('File not found or is a directory', 'danger')
        return redirect(url_for('dashboard', path=os.path.dirname(path)))

    rename_form = RenameFileForm()
    if rename_form.validate_on_submit():
        new_name = secure_filename(rename_form.new_name.data)
        new_path = os.path.join(os.path.dirname(file_path), new_name)
        os.rename(file_path, new_path)
        flash('File renamed successfully!', 'success')
        return redirect(url_for('dashboard', path=os.path.dirname(new_path)))

    form = EditFileForm()
    if form.validate_on_submit():
        with open(file_path, 'w') as f:
            lines = form.content.data.splitlines()
            f.write('\n'.join(lines))
        flash('File saved successfully!', 'success')
        return redirect(url_for('dashboard'))


    if request.method == 'GET':
        if file_path.lower().endswith(('.webp', '.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return send_file(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                form.content.data = f.read()
            return render_template('edit_file.html', form=form, file_path=path, rename_form=rename_form)

@app.route('/run_command', methods=['POST'])
def run_command_api():
    command = request.json.get('command')
    if command:
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            return jsonify({'stdout': result.stdout, 'stderr': result.stderr})
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'プロセスがタイムアウトしました'}), 500
        except Exception as e:
            return jsonify({'error': f'コマンドの実行中にエラーが発生しました：{str(e)}'}), 500
    else:
        return jsonify({'error': 'コマンドが提供されていません'}), 400
    
@app.route('/open_console', methods=['GET', 'POST'])
def open_console():
    form = CommandForm()
    return render_template('open_console.html', form=form)

@app.before_request
def before_request():
    if not current_user.is_authenticated and request.endpoint != 'login':
        return redirect(url_for('login', next=request.endpoint))

if __name__ == '__main__':
    app.run(debug=True)
