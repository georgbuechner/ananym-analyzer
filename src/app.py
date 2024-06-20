import os
import urllib.parse
from flask import Flask, flash, render_template, redirect, request, send_from_directory
from dmanager.dmanager import DManager
from dmanager.dmodels import AnalysisOpts
from dmanager.models import Sweep
from service import Service
from utils import stem
from extractor.functions import Peaks
from dotenv import load_dotenv

UPLOAD_FOLDER = 'data/'

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

service = Service(UPLOAD_FOLDER)

@app.route("/")
def main(): 
    return render_template("index.html")

@app.route("/data/raw")
def data_raw(): 
    return render_template(
        "data/raw.html", 
        data=service.get_raw(), 
        all_tags=service.dmanager.all_tags
    )

@app.route("/data/sweeps")
def data_sweeps(): 
    return render_template(
        "data/sweeps.html", 
        data=service.get_sweeps(), 
        all_tags=service.dmanager.all_tags
    )

@app.route("/data/analysis/", defaults = {"date": "", "file": ""})
@app.route("/data/analysis/<date>/<file>", methods=["GET", "POST"])
def analysis(date: str = "", file: str = ""): 
    if date == "" and file == "": 
        return render_template("data/analysis.html", data=service.get_analysis())
    if request.method == 'POST':
        print(request.form)
        try: 
            ylim = (
                float(request.form.get("ylim_min")), float(request.form.get("ylim_max"))
            )
        except: 
            ylim = None 
        msg, msg_type = service.do_analysis(
            date=date, 
            filename=file, 
            opt=AnalysisOpts(int(request.form.get("opt") or 1)),
            start=int(request.form.get("sweep_range"))-1,
            end=int(request.form.get("sweep_range_to")),
            ylim=ylim,
        )
        flash(msg, msg_type)
    sweep = Sweep(service.dmanager, date, file)
    only_favorites = request.args.get("only_favorites") == "True" or False
    return render_template(
        "analysis/analysis.html",
        date=date, 
        name=sweep.name,
        filename=sweep.filename,
        version=sweep.version,
        tags=sweep.tags,
        all_tags=service.dmanager.all_tags,
        analysis=service.get_single_analysis(
            date, file, only_favorites=only_favorites
        ),
        num_sweeps=service.num_sweeps(date, file),
        favorites = service.dmanager.favorites,
        projects=sorted(service.dmanager.projects.keys())

    )


@app.route("/upload", methods=["GET", "POST"])
def upload(): 
    if request.method == 'POST':
        # check if the post request has the file part
        if 'igorFile' not in request.files:
            flash('No file part', 'danger')
        else:
            file = request.files['igorFile']
            date = request.form.get("creationDate");
            tags = request.form.get("tags");
            extract = "unpackIgorCheck" in request.form
            msg, msg_type = service.upload_raw(file, date, extract, tags)
            flash(msg, msg_type)
    return render_template("upload/upload.html", all_tags=service.dmanager.all_tags)

@app.route("/projects")
def projects(): 
    def safe(path: str): 
        return urllib.parse.quote(path, safe='')

    return render_template(
        "projects/projects.html", 
        projects=sorted(service.dmanager.projects.keys()),
        safe=safe
    )

@app.route("/projects/<path:project_name>")
def project(project_name: str): 
    if project_name in service.dmanager.projects:
        return render_template(
            "projects/project.html", 
            project_name=project_name,
            project=service.dmanager.projects[project_name],
        )
    else: 
        return redirect("/projects")

@app.route("/api/projects/add", methods=["POST"])
def add_project(): 
    name = request.form.get("project_name") or ""
    parent = request.form.get("project_parent") or ""
    flash(*service.dmanager.add_project(os.path.join(parent, name)))
    return redirect("/projects")

@app.route("/api/projects/del", methods=["POST"])
def del_project(): 
    name = request.form.get("project_name") or ""
    flash(*service.dmanager.del_project(name))
    return redirect("/projects")

@app.route("/handle/raw", methods=["POST"])
def handle_raw(): 
    date = request.form.get('dir')
    file = request.form.get("file")
    if "unpack-raw-data" in request.form:
        msg, msg_type = service.unpack_raw(date, file)
    elif "delete-raw-data" in request.form: 
        msg, msg_type = service.delete_data(service.dir_raw, date, file)
    else: 
        msg, msg_type = ("Unknown option", "danger")
    flash(msg, msg_type)
    return redirect("/data/raw")

@app.route("/handle/sweeps", methods=["POST"])
def handle_sweeps(): 
    date = request.form.get('dir')
    file = request.form.get("file")
    if "analyze-sweeps" in request.form:
        return redirect(f"/data/analysis/{date}/{stem(file)}")
    elif "delete-sweeps" in request.form: 
        msg, msg_type = service.delete_data(service.dir_sweeps, date, file)
    else: 
        msg, msg_type = ("Unknown option", "danger")
    flash(msg, msg_type)
    return redirect("/data/sweeps")

@app.route("/handle/analysis", methods=["POST"])
def handle_analysis(): 
    date = request.form.get('dir')
    file = request.form.get("file")
    if "view-all" in request.form:
        return redirect(f"/data/analysis/{date}/{stem(file)}")
    elif "delete-all" in request.form: 
        msg, msg_type = service.delete_data(service.dir_analysis, date, file)
    else: 
        msg, msg_type = ("Unknown option", "danger")
    flash(msg, msg_type)
    return redirect("/data/analysis")

@app.route("/handle/analysis/peaks", methods=["POST"])
def analyse_peaks(): 
    peaks_info = Peaks(
        start=float(request.form["peak_start"]), 
        step=float(request.form["peak_step"]), 
        interval=float(request.form["peak_interval"]), 
        num_intervals=int(request.form["peak_num_intervals"])
    )
    date = request.form.get("date")
    filename = request.form.get("filename")
    _ = service.calc_peaks(request.form.get('path'), peaks_info)
    sweep = Sweep(service.dmanager, date, filename)
    only_favorites = request.args.get("only_favorites") == "True" or False
    return render_template(
        "analysis/analysis.html",
        date=date, 
        name=sweep.name,
        filename=sweep.filename,
        version=sweep.version,
        tags=sweep.tags,
        all_tags=service.dmanager.all_tags,
        analysis=service.get_single_analysis(
            date, filename, only_favorites=only_favorites
        ),
        num_sweeps=service.num_sweeps(date, filename),
        favorites=service.dmanager.favorites,
        projects=sorted(service.dmanager.projects.keys())
    )


@app.route("/delete/analysis", methods=["POST"])
def delete_analysis(): 
    path = request.form.get('path')
    date = request.form.get('date')
    filename = request.form.get('filename')
    print(request.form)
    try:
        os.remove(path)
        os.remove(path.replace("png", "svg"))
        os.remove(path.replace("png", "json"))
        flash("Successfully deleted analysis.", "success")
    except Exception as e:
        flash(f"Failed: {repr(e)}.", "success")
    return redirect(f"/data/analysis/{date}/{filename}")

@app.route("/tags/update/", methods=["POST"])
def add_tag(): 
    print(request.form)
    path = stem(request.form.get('path'))
    print("PATH: ", path)
    tag = request.form.get('tag')
    service.add_tag_to_entry(path, tag)
    return "", 200

@app.route("/tags/remove/", methods=["POST"])
def remove_tag(): 
    print(request.form)
    path = stem(request.form.get('path'))
    tag = request.form.get('tag')
    service.remove_tag_from_entry(path, tag)
    return "", 200


@app.route('/data/analysis/<date>/<name>/<filename>')
def serve_image(date, name, filename):
    # Specify the path to the directory where your images are stored
    image_directory = os.path.abspath(os.path.join(service.dir_analysis, date, name))
    return send_from_directory(image_directory, filename)

@app.route('/data/analysis/<date>/<name>/<plug_dir>/<plugin>/<sweep>')
def serve_image_plug(date, name, plug_dir, plugin, sweep):
    # Specify the path to the directory where your images are stored
    image_directory = os.path.abspath(
        os.path.join(service.dir_analysis, date, name, plug_dir, plugin)
    )
    print("Got img dir: ", image_directory)
    return send_from_directory(image_directory, sweep)

@app.route('/api/favorites/add/<path:path>', methods=["POST"])
def api_add_favorite(path: str):
    # Specify the path to the directory where your images are stored
    service.dmanager.add_favorite(path)
    return "", 200

@app.route('/api/favorites/remove/<path:path>', methods=["POST"])
def api_del_favorite(path: str):
    # Specify the path to the directory where your images are stored
    service.dmanager.del_favorite(path)
    return "", 200

@app.route("/api/search/<location>/", defaults = {"tags":""})
@app.route("/api/search/<location>/<tags>")
def search(location: str, tags: str): 
    get_data_funcs = {
        "raw": service.get_raw, 
        "sweeps": service.get_sweeps, 
        "analysis": service.get_analysis
    }
    if len(tags) > 0: 
        data = service.get_searched(get_data_funcs[location], tags)
    else: 
        data = get_data_funcs[location]()
    return render_template(
        f"data/{location}_content.html", 
        data=data, 
        all_tags=service.dmanager.all_tags,
        collapsed=tags==""
    )

if __name__ == "__main__": 
    load_dotenv()
    app.run(debug=True, port=os.getenv('ANA_LZER_PORT'))
