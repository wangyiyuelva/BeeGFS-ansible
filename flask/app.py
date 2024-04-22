import os
from flask import Flask, flash, request, redirect, send_from_directory, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/beegfs/data/input/'
OUTPUT_FOLDER = '/beegfs/data/output/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.secret_key = b'ae40ba2c00ea0a02a05a304c76d04a40dd001125e0718a9fa46b4f2d5c7ce777'

@app.route('/')
def upload_form():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    else:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # print('upload_video filename: ' + filename)
        flash('Video successfully uploaded and displayed below')
        return render_template('index.html', filename=filename)

@app.route("/download/<path:filename>")
def display_video(filename):
    return send_from_directory(
        app.config['OUTPUT_FOLDER'], filename, as_attachment=True
    )

@app.route("/output/<path:filename>")
def display_video(filename):
    output_name = secure_filename(f"{filename}DLC_snapshot-700000_labeled.mp4")
    output_path =  os.path.join(app.config['OUTPUT_FOLDER'], output_name)
    return render_template('output.html', filename=output_path)

@app.route('/Log/<path:log_number>')
def display_log(log_number):
    try:
        filename = f'static/{log_number}.log'  # Construct filename based on log_number
        log_content = ''
        with open(filename, 'r') as f:
            log_content = f.read()
        return render_template('log.html', log_content=log_content)
    except FileNotFoundError:
        return "Logfile not found!", 404

