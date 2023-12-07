import os
from flask import Flask, flash, render_template, redirect, request
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'data/raw/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3'}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    print(filename, filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def main(): 
    return render_template("index.html")

@app.route("/data")
def data(): 
    return render_template("data.html")

@app.route("/upload", methods=["GET", "POST"])
def upload(): 
    if request.method == 'POST':
        print(request.files)
        # check if the post request has the file part
        if 'igorFile' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['igorFile']
        date = request.form.get("creationDate");
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '' or date == '':
            flash('No file or creation-date', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Create date-dir if not exists
            path_to_date = os.path.join(app.config['UPLOAD_FOLDER'], date)
            if not os.path.exists(path_to_date): 
                os.makedirs(path_to_date) 
            # Store file if not exists
            path_to_file = os.path.join(
                path_to_date, secure_filename(file.filename)
            )
            if os.path.exists(path_to_file): 
                flash('File already exists', 'danger')
            else:
                file.save(path_to_file)
                flash('Upload success!', 'success')
        else: 
            flash('Invalid file type!', 'danger')
    return render_template("upload.html")


if __name__ == "__main__": 
    app.run(debug=True)
