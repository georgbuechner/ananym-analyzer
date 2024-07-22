import io
import os
import zipfile
from typing import List, Tuple
import urllib.parse
from flask import Flask, flash, render_template, redirect, request, send_file, send_from_directory
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
        msg, msg_type = service.do_analysis(
            date=date, 
            filename=file, 
            opt=AnalysisOpts(int(request.form.get("opt") or 1)),
            start=int(request.form.get("sweep_range"))-1,
            end=int(request.form.get("sweep_range_to")),
            ylim=_get_ylim(request)
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
        project = service.dmanager.projects[project_name]
        return render_template(
            "projects/project.html", 
            project_name=project_name,
            project=project,
            analysis=service.get_project_analysis_objs(project),
            project_analysis=service.dmanager.get_project_analysis(project_name)
        )
    else: 
        return redirect("/projects")

@app.route("/api/projects/add", methods=["POST"])
def add_project(): 
    name = request.form.get("project_name") or ""
    parent = request.form.get("project_parent") or ""
    flash(*service.dmanager.add_project(os.path.join(parent, name)))
    return redirect("/projects")

@app.route("/api/projects/rename", methods=["POST"])
def rename_project(): 
    name = request.form.get("project_name") or ""
    parent = request.form.get("project_parent") or ""
    cur_name = request.form.get("cur_project_name") or ""
    flash(*service.dmanager.rename_project(cur_name, os.path.join(parent, name)))
    return redirect("/projects")

@app.route("/api/projects/del", methods=["POST"])
def del_project(): 
    name = request.form.get("project_name") or ""
    flash(*service.dmanager.del_project(name))
    return redirect("/projects")

@app.route("/api/projects/add_analysis", methods=["POST"])
def add_to_project(): 
    project = request.args.get("project") or ""
    analysis_path = request.args.get("path") or ""
    print(f"Got project: {project} and analysis_path: {analysis_path}")
    if project in service.dmanager.projects: 
        msg, code = service.dmanager.projects[project].add(analysis_path)
    else:
        msg, code = (f"Project {project} not found!", 404)
    return msg, code

@app.route("/api/projects/remove_analysis", methods=["POST"])
def remove_from_project(): 
    project = request.args.get("project") or ""
    analysis_path = request.args.get("path") or ""
    print(f"Got project: {project} and analysis_path: {analysis_path}")
    if project in service.dmanager.projects: 
        msg, code = service.dmanager.projects[project].remove(analysis_path)
    else:
        msg, code = (f"Project {project} not found!", 404)
    return msg, code

@app.route("/api/projects/stack", methods=["POST"])
def stack_project_analysis(): 
    project_name = request.form.get("project_name") or ""
    flash(
        *service.project_stack_analysis(project_name, ylim=_get_ylim(request))
    )
    return redirect(f"/projects/{project_name}")

@app.route("/api/projects/del/stacked", methods=["POST"])
def del_stacked_project_analysis(): 
    path = request.form.get("path") or ""
    project_name = request.form.get("project_name") or ""
    try:
        os.remove(f"{path}.png")
        os.remove(f"{path}.svg")
        flash("Successfully deleted project analysis.", "success")
    except Exception as e:
        flash(f"Failed: {repr(e)}.", "success")
    return redirect(f"/projects/{project_name}")

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
def serve_image_analysis(date, name, filename):
    # Specify the path to the directory where your images are stored
    image_directory = os.path.abspath(os.path.join(service.dir_analysis, date, name))
    return send_from_directory(image_directory, filename)

@app.route('/data/analysis/<date>/<name>/<plug_dir>/<plugin>/<sweep>')
def serve_image_plug(date, name, plug_dir, plugin, sweep):
    # Specify the path to the directory where your images are stored
    image_directory = os.path.abspath(
        os.path.join(service.dir_analysis, date, name, plug_dir, plugin)
    )
    return send_from_directory(image_directory, sweep)

@app.route('/data/projects/<path:project_analysis>')
def serve_image_project(project_analysis: str):
    # Specify the path to the directory where your images are stored
    absolute_path = os.path.abspath(
        os.path.join(service.dmanager.dir_projects, project_analysis)
    )
    return send_from_directory(*os.path.split(absolute_path))

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

@app.route("/api/create/minimal/<project_name>")
def create_project_minimal(project_name: str): 
# List of file paths to include in the zip archive
    file_paths = [
        f"{stem(a)}.json" for a in service.dmanager.projects[project_name].analysis 
    ]
    files_with_name = { 
        f"{a[14:24]}_{stem(a[a.rfind("/")+1:])}":a[a.rfind("/")+1:] for a in file_paths 
    }
    file_paths.append("src/extractor/functions.py")
    file_paths.append("src/templates/minimal/requirements.txt")
    file_paths.append("src/templates/minimal/README.md")
    minimal_py = render_template('minimal/minimal.py', analysis=files_with_name)

    # Create the zip archive
    zip_buffer = create_zip_archive(file_paths, minimal_py)

    # Send the zip file
    return send_file(
        zip_buffer, 
        mimetype='application/zip', 
        as_attachment=True, 
        download_name=f"analyzer_project_{project_name}"
    )

def create_zip_archive(file_paths: List[str], minimal_py: str):
    # Create a BytesIO object to hold the zip file in memory
    zip_buffer = io.BytesIO()

    # Create a zip file object
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            # Add each file to the zip archive
            zip_file.write(file_path, arcname=file_path.split('/')[-1])
        # Add the rendered minimal.py file to the zip archive
        zip_file.writestr('run.py', minimal_py)

    # Ensure the buffer position is at the beginning
    zip_buffer.seek(0)

    return zip_buffer


def _get_ylim(req) -> Tuple[float, float] | None: 
    try: 
        return (
            float(req.form.get("ylim_min")), float(req.form.get("ylim_max"))
        )
    except: 
        return None 

if __name__ == "__main__": 
    load_dotenv()
    app.run(debug=True, port=os.getenv('ANA_LZER_PORT'))
