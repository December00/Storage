import os
from flask import Flask, request, jsonify, send_from_directory, abort, make_response
from datetime import datetime

app = Flask(__name__)
STORAGE_DIR = 'storage'

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)


@app.route('/', methods=['GET'])
def list_root():
    return list_directory('')


@app.route('/<path:filepath>', methods=['GET', 'PUT', 'DELETE', 'HEAD'])
def handle_file(filepath):
    abs_path = os.path.join(STORAGE_DIR, filepath)

    if request.method == 'GET':
        if os.path.isdir(abs_path):
            return list_directory(filepath)
        else:
            if os.path.exists(abs_path):
                return send_from_directory(STORAGE_DIR, filepath)
            else:
                abort(404, description="File not found")

    elif request.method == 'PUT':
        dir_path = os.path.dirname(abs_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(abs_path, 'wb') as f:
            f.write(request.data)

        response = make_response(jsonify({
            'message': f'File {filepath} successfully uploaded/updated'
        }))
        response.status_code = 201
        return response

    elif request.method == 'DELETE':
        if os.path.exists(abs_path):
            if os.path.isdir(abs_path):
                try:
                    os.rmdir(abs_path)
                    message = f'Directory {filepath} successfully deleted'
                except OSError:
                    return jsonify({
                        'status': 'error',
                        'message': 'Directory is not empty'
                    }), 400
            else:
                os.remove(abs_path)
                message = f'File {filepath} successfully deleted'

            response = make_response(jsonify({
                'message': message
            }))
            response.status_code = 204
            return response
        else:
            abort(404, description="File or directory not found")

    elif request.method == 'HEAD':
        if os.path.exists(abs_path) and not os.path.isdir(abs_path):
            stats = os.stat(abs_path)
            last_modified = datetime.fromtimestamp(stats.st_mtime).strftime('%d.%m.%Y %H:%M:%S')
            return '', 200, {
                'Content-Length': stats.st_size,
                'Last-Modified': last_modified
            }
        else:
            abort(404, description="File not found")


def list_directory(rel_path):
    abs_path = os.path.join(STORAGE_DIR, rel_path)
    if not os.path.exists(abs_path):
        abort(404, description="Directory not found")

    if not os.path.isdir(abs_path):
        abort(400, description="Path is not a directory")

    files = []
    dirs = []

    for name in os.listdir(abs_path):
        full_path = os.path.join(abs_path, name)
        stats = os.stat(full_path)
        item = {
            'name': name,
            'size': stats.st_size,
            'last_modified': datetime.fromtimestamp(stats.st_mtime).strftime('%d.%m.%Y %H:%M:%S')
        }
        if os.path.isdir(full_path):
            dirs.append(item)
        else:
            files.append(item)

    return jsonify({
        'current_path': rel_path,
        'directories': dirs,
        'files': files
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)