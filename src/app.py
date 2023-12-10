import os
from flask import Flask, flash, render_template, redirect, request, send_from_directory
from service import Service
from utils import stem

UPLOAD_FOLDER = 'data/'

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

service = Service(UPLOAD_FOLDER)

@app.route("/")
def main(): 
    return render_template("index.html")

@app.route("/data/raw")
def data_raw(): 
    return render_template("data_raw.html", data=service.get_raw())

@app.route("/data/sweeps")
def data_sweeps(): 
    return render_template("data_sweeps.html", data=service.get_sweeps())

@app.route("/upload", methods=["GET", "POST"])
def upload(): 
    if request.method == 'POST':
        # check if the post request has the file part
        if 'igorFile' not in request.files:
            flash('No file part', 'danger')
        else:
            file = request.files['igorFile']
            date = request.form.get("creationDate");
            extract = "unpackIgorCheck" in request.form
            msg, msg_type = service.upload_raw(file, date, extract)
            flash(msg, msg_type)
    return render_template("upload.html")

@app.route("/analysis/<date>/<file>", methods=["GET", "POST"])
def analysis(date: str, file: str): 
    if request.method == 'POST':
        print(request.form)
        service.do_analysis(date, file, request.form.get("sweep_selection"))
    filename, name, version = service.split_sweeps_name(file)
    return render_template(
        "analysis.html",
        date=date, 
        name=name,
        filename=filename,
        version=version,
        analysis=service.get_analysis(date, file)
    )

@app.route("/handle/raw", methods=["POST"])
def handle_raw(): 
    print(request.form)
    date = request.form.get('dir')
    file = request.form.get("file")
    if "unpack-raw-data" in request.form:
        msg, msg_type = service.unpack_raw(date, file)
    elif "delete-raw-data" in request.form: 
        msg, msg_type = service.delete_data(service.dir_raw, date, file)
    flash(msg, msg_type)
    return redirect("/data/raw")

@app.route("/handle/sweeps", methods=["POST"])
def handle_sweeps(): 
    print(request.form)
    date = request.form.get('dir')
    file = request.form.get("file")
    if "analyze-sweeps" in request.form:
        return redirect(f"/analysis/{date}/{stem(file)}")
    elif "delete-sweeps" in request.form: 
        msg, msg_type = service.delete_data(service.dir_sweeps, date, file)
    flash(msg, msg_type)
    return redirect("/data/sweeps")

@app.route('/data/analysis/<date>/<name>/<filename>')
def serve_image(date, name, filename):
    # Specify the path to the directory where your images are stored
    image_directory = os.path.abspath(os.path.join(service.dir_analysis, date, name))
    print("Got image path: ", image_directory, filename)
    print("exists? ", os.path.exists(os.path.join(image_directory, filename)))
    return send_from_directory(image_directory, filename)


if __name__ == "__main__": 
    app.run(debug=True)
