from contextlib import closing
from flask import (
	Flask, 
	current_app, 
	flash, 
	g, 
	jsonify, 
	redirect, 
	render_template, 
	request,
	url_for
)
from werkzeug.utils import secure_filename
import os
import sqlite3


ALLOWED_EXTENSIONS = { 'txt', }

app = Flask(__name__)
app.config.from_mapping(
	SECRET_KEY='your secret here', 
	MAX_CONTENT_LENGTH=16 * 1024 * 1024, 
	UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'), 
	DATABASE=os.path.join(app.instance_path, 'file_uploads.db')
)
print(app.instance_path)
def get_db():
	if 'db' not in g:
		g.db = sqlite3.connect(
			current_app.config['DATABASE'] 
		)
	return g.db

@app.teardown_appcontext
def close_db(exception):
	db = g.pop('db', None)
	if db is not None:
		db.close()


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
with app.app_context():
	db = get_db()
	with closing(db.cursor()) as c:
		c.execute('''CREATE TABLE IF NOT EXISTS words (
				id INTEGER PRIMARY KEY AUTOINCREMENT, 
				word TEXT NOT NULL, 
				filename TEXT NOT NULL, 
				filepath TEXT NOT NULL
			)''')
	db.commit()


# Health check to see if the service is active
@app.route('/healthCheck')
def check_status():
	return jsonify({
		'healthCheck': 'Flask service is up and running!'
	}), 200


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		
		file = request.files['file']
		if file.filename == '':
			flash('No file selected for uploading')
			return redirect(request.url)
		
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
			file.save(filepath)

			# Read content of the file and split into words
			with open(filepath, 'r') as f:
				content = f.read()
				words = content.split()
			
			# Insert each word into the SQLite database
			db = get_db()
			with closing(db.cursor()) as c:
				c.executemany(
					'INSERT INTO words (word, filename, filepath) VALUES (?, ?, ?)', 
					[(word, filename, filepath,) for word in words]
				)
			db.commit()
			
			flash('File successfully uploaded and words saved to database')
			return redirect(url_for('.upload'))
		else:
			flash('Allowed file types are txt')
			return redirect(request.url)

	return render_template('upload.html')

@app.route('/word/<int:id>')
def get_word_by_id(id):
	db = get_db()
	with closing(db.cursor()) as c:
		c.execute("SELECT word FROM words WHERE id=?", (id,))
		word = c.fetchone()
	
	if word:
		return jsonify({'id': id, 'word': word[0]}), 200
	else:
		return jsonify({'error': 'Word not found'}), 404
