from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__, template_folder="templates")

@app.route("/")
def serve_index():
    return render_template("index.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("assets", filename)

@app.route("/car-photo/<path:filename>")
def serve_car_photo(filename):
    return send_from_directory("car-photo", filename)

@app.route("/car-info/<car_folder>/")
def serve_car_info(car_folder):
    car_path = os.path.join("templates", "car-info", car_folder)
    html_file = os.path.join(car_path, "index.html")
    if os.path.exists(html_file):
        return render_template(f"car-info/{car_folder}/index.html")
    else:
        return "File not found", 404

@app.route("/car-info/<car_folder>/<path:filename>")
def serve_car_info_file(car_folder, filename):
    car_path = os.path.join("templates", "car-info", car_folder)
    if os.path.exists(car_path):
        return send_from_directory(car_path, filename)
    else:
        return "File not found", 404

if __name__ == "__main__":
    print("Server listening on port 8080...")
    app.run(port=8080)
