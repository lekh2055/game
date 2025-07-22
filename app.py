import os
import urllib.parse # URL encoding paths ke liye
from flask import Flask, render_template, send_from_directory, abort, url_for

app = Flask(__name__)

# Aapka local path jahan photos aur videos hain
# NOTE: Windows mein backslashes ko forward slashes mein badal dein
# ya raw string use karein (r'A:\khirbhan\PHOTOMEGHNATH')
# Is path ko apne hisaab se badalna na bhoolein!
MEDIA_FOLDER = 'A:/khirbhan' # <--- YAHAN USER DWARA DIYA GAYA PATH HAI

# Check karein ki media folder exist karta hai
if not os.path.exists(MEDIA_FOLDER):
    # Yahan f-string ke andar ke curly braces ko double kiya gaya hai
    print(f"\n!!! WARNING: MEDIA_FOLDER '{{MEDIA_FOLDER}}' exist nahi karta hai. Kripya sahi path select karein. !!!\n")
    # Application chalegi, lekin files nahi dikhengi.

@app.route('/')
@app.route('/<path:subpath>')
def browse(subpath=''):
    print(f"\n--- Request Debug ---")
    print(f"DEBUG: MEDIA_FOLDER set to: '{MEDIA_FOLDER}'")
    print(f"DEBUG: Requested URL subpath: '{subpath}'")

    # Security ke liye, yeh sunishchit karein ki requested subpath MEDIA_FOLDER ke andar hi rahe
    full_path = os.path.join(MEDIA_FOLDER, subpath)
    full_path = os.path.normpath(full_path) # '..' jaise paths ko handle karne ke liye normalize karein

    normalized_media_folder = os.path.normpath(MEDIA_FOLDER)

    print(f"DEBUG: Constructed full path: '{full_path}'")
    print(f"DEBUG: Normalized MEDIA_FOLDER: '{normalized_media_folder}'")
    print(f"DEBUG: Check if full path starts with MEDIA_FOLDER: {full_path.startswith(normalized_media_folder)}")

    if not full_path.startswith(normalized_media_folder):
        print(f"SECURITY ALERT: Attempted path traversal outside MEDIA_FOLDER: '{full_path}'")
        abort(403) # Forbidden access

    if not os.path.exists(full_path):
        print(f"ERROR: Path does not exist on server: '{full_path}'")
        abort(404) # Not Found

    if not os.path.isdir(full_path):
        print(f"ERROR: Path is a file, not a directory: '{full_path}'. Expected a directory for browsing.")
        # Agar yeh ek file hai aur browse route hit hua hai, toh 404 ya appropriate action
        abort(404) # Not Found, as this route is for directories

    items = []
    try:
        # Directory ke contents ko list karein
        for item_name in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, item_name)
            
            # relpath calculation should be relative to MEDIA_FOLDER
            relative_item_path = os.path.relpath(item_path, MEDIA_FOLDER)
            encoded_item_path = urllib.parse.quote(relative_item_path) # URL encode path

            item_type = 'unknown'
            if os.path.isdir(item_path):
                item_type = 'folder'
            elif os.path.isfile(item_path):
                file_extension = os.path.splitext(item_name)[1].lower()
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    item_type = 'image'
                elif file_extension in ['.mp4', '.avi', '.mkv', '.mov', '.webm']:
                    item_type = 'video'
                else:
                    item_type = 'file' # Anya files ke liye generic file type

            # Yahan dictionary ke curly braces ko double kiya gaya hai
            items.append({
                'name': item_name,
                'type': item_type,
                'relative_path': relative_item_path, # MEDIA_FOLDER ke sapeksh path
                'encoded_path': encoded_item_path # Links ke liye URL encoded path
            })
    except PermissionError:
        print(f"PERMISSION ERROR: Server does not have permission to read directory: '{full_path}'")
        abort(403) # Forbidden
    except Exception as e:
        print(f"UNEXPECTED ERROR while listing directory '{full_path}': {e}")
        abort(500) # Internal Server Error

    # "Go Up" button ke liye parent path determine karein
    current_relative_path = os.path.relpath(full_path, MEDIA_FOLDER)
    parent_relative_path = os.path.dirname(current_relative_path)
    encoded_parent_path = urllib.parse.quote(parent_relative_path) if parent_relative_path != '.' else ''

    print(f"DEBUG: Items found: {len(items)}")
    print(f"--- End Request Debug ---\n")

    return render_template('index.html',
                           items=items,
                           current_path=subpath,
                           encoded_parent_path=encoded_parent_path,
                           is_root= (subpath == '' or subpath == '.'))

@app.route('/media_file/<path:filename>')
def serve_media_file(filename):
    print(f"\n--- Media File Request Debug ---")
    print(f"DEBUG: Requested media filename: '{filename}'")
    
    # Security check: Sunishchit karein ki requested file MEDIA_FOLDER ke andar hai
    full_file_path = os.path.join(MEDIA_FOLDER, filename)
    full_file_path = os.path.normpath(full_file_path)

    normalized_media_folder = os.path.normpath(MEDIA_FOLDER)

    print(f"DEBUG: Constructed full file path: '{full_file_path}'")
    print(f"DEBUG: Check if full file path starts with MEDIA_FOLDER: {full_file_path.startswith(normalized_media_folder)}")

    if not full_file_path.startswith(normalized_media_folder):
        print(f"SECURITY ALERT: Attempted file traversal outside MEDIA_FOLDER: '{full_file_path}'")
        abort(403) # Forbidden access

    # Directory aur base filename extract karein
    directory = os.path.dirname(full_file_path)
    base_filename = os.path.basename(full_file_path)

    if not os.path.isfile(full_file_path):
        print(f"ERROR: Media file does not exist: '{full_file_path}'")
        abort(404) # Not Found
    
    print(f"DEBUG: Serving file from directory: '{directory}', filename: '{base_filename}'")
    print(f"--- End Media File Request Debug ---\n")
    return send_from_directory(directory, base_filename)

if __name__ == '__main__':
    # debug=True se changes automatic apply honge aur errors dikhenge
    # host='0.0.0.0' ka matlab hai ki application aapke network ke sabhi available IPs par chalegi.
    # Port 5000 default hai, aap ise badal bhi sakte hain agar zaroorat ho.
    app.run(debug=True, host='0.0.0.0', port=5000)
