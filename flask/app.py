import os
from flask import Flask, flash, request, redirect, send_from_directory, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/beegfs/data/input/'
OUTPUT_FOLDER = '/beegfs/data/output/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['LOG_FOLDER'] = 'static/'
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
        outputfilename = filename[:-4]
        return render_template('index.html', filename=filename, output_file=outputfilename, plot=outputfilename)

@app.route("/download/<path:filename>")
def display_video(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], filename, as_attachment=True
    )

@app.route("/output/<path:output_file>")
def display_output(output_file):
    filename = f'{output_file}wildDLC_snapshot-700000_labeled.mp4'
    return send_from_directory(
        app.config['OUTPUT_FOLDER'], filename, as_attachment=True
    )

@app.route("/plot/<path:plot>")
def display_plot(plot):
    plot_name = f'plot-poses/{plot}wild/trajectory.png'
    return send_from_directory(
        app.config['OUTPUT_FOLDER'], plot_name, as_attachment=True
    )

def get_log_filenames():
    log_files = []
    log_folder = app.config['LOG_FOLDER']
    for filename in os.listdir(log_folder):
        if filename.endswith('.log'):
            log_files.append(filename)
    return log_files

@app.route('/Log')
def display_logs():
    log_filenames = get_log_filenames()
    logs = {}
    for filename in log_filenames:
        with open(f"{app.config['LOG_FOLDER']}/{filename}", 'r') as f:
            log_content = f.read()
            logs[filename] = log_content
    return render_template('log.html', logs=logs)

# @app.route('/Log/<path:log_number>')
# def display_log(log_number):
#     try:
#         filename = f'static/{log_number}.log'
#         log_content = ''
#         with open(filename, 'r') as f:
#             log_content = f.read()
#         return render_template('log.html', log_content=log_content)
#     except FileNotFoundError:
#         return "Logfile not found!", 404


