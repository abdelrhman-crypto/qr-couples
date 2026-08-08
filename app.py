import os
import uuid
import json
import re
from flask import Flask, render_template, request, redirect, url_for
import qrcode

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['QR_FOLDER'] = os.path.join('static', 'qrcodes')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

DB_FILE = 'database.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def sanitize_filename(name):
    # تنظيف الاسم المخصص من المسافات والرموز غير المسموحة
    name = name.strip().replace(' ', '_')
    name = re.sub(r'[^\w\-]', '', name)
    return name if name else str(uuid.uuid4())[:8]

@app.route('/')
def admin_panel():
    return render_template('admin.html')

@app.route('/create', methods=['POST'])
def create_memory():
    # استقبال اسم العميل / اسم الصفحة المخصص
    custom_name = request.form.get('custom_name', '').strip()
    
    if custom_name:
        page_id = sanitize_filename(custom_name)
    else:
        page_id = str(uuid.uuid4())[:8]
    
    bg_type = request.form.get('bg_type', 'color')
    bg_color = request.form.get('bg_color', '#fff5f5')
    
    bg_image_url = None
    if bg_type == 'image':
        bg_file = request.files.get('bg_image')
        if bg_file and bg_file.filename != '':
            bg_filename = f"bg_{page_id}_{bg_file.filename}"
            bg_file.save(os.path.join(app.config['UPLOAD_FOLDER'], bg_filename))
            bg_image_url = f"/static/uploads/{bg_filename}"

    song_file = request.files.get('song')
    song_path = None
    if song_file and song_file.filename != '':
        song_filename = f"{page_id}_{song_file.filename}"
        song_file.save(os.path.join(app.config['UPLOAD_FOLDER'], song_filename))
        song_path = f"/static/uploads/{song_filename}"

    media_files = request.files.getlist('media')
    texts = request.form.getlist('texts')
    
    moments = []
    for i, file in enumerate(media_files):
        if file and file.filename != '':
            filename = f"{page_id}_{i}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            ext = file.filename.split('.')[-1].lower()
            is_video = ext in ['mp4', 'webm', 'ogg', 'mov']
            
            media_url = f"/static/uploads/{filename}"
            text = texts[i] if i < len(texts) else ""
            moments.append({
                "url": media_url, 
                "is_video": is_video, 
                "text": text
            })

    # حفظ الصفحة في قاعدة البيانات
    db = load_db()
    db[page_id] = {
        "custom_name": custom_name,
        "bg_type": bg_type,
        "bg_color": bg_color,
        "bg_image_url": bg_image_url,
        "song_url": song_path,
        "moments": moments
    }
    save_db(db)

    generate_qr(page_id)
    return redirect(url_for('show_result', page_id=page_id))

@app.route('/result/<page_id>')
def show_result(page_id):
    return f'''
    <div style="text-align:center; font-family:sans-serif; padding:50px;">
        <h2>✅ تم إنشاء الصفحة وتسمية الـ QR بنجاح!</h2>
        <p><b>معرف الصفحة / اسم الصورة:</b> <code>{page_id}</code></p>
        <p><b>رابط الصفحة:</b> <a href="/p/{page_id}" target="_blank">اضغط هنا لمعاينة الصفحة</a></p>
        <img src="/static/qrcodes/{page_id}.png" style="width:200px; border:1px solid #ccc; padding:10px;"><br><br>
        <p><small>مسار صورة الـ QR المسجلة: <code>static/qrcodes/{page_id}.png</code></small></p><br>
        <a href="/">+ إنشاء صفحة عميل جديد</a>
    </div>
    '''

@app.route('/p/<page_id>')
def show_couple_page(page_id):
    db = load_db()
    data = db.get(page_id)
    if not data:
        return "الصفحة غير موجودة", 404
    return render_template('couple.html', data=data)

def generate_qr(page_id):
    domain = request.host_url.rstrip('/')
    target_url = f"{domain}/p/{page_id}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # حفظ صورة الـ QR باسم العميل المخصص
    img.save(os.path.join(app.config['QR_FOLDER'], f"{page_id}.png"))

if __name__ == '__main__':
    app.run(debug=True)