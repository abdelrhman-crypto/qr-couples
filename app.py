import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
import qrcode

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['QR_FOLDER'] = os.path.join('static', 'qrcodes')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

database = {}

@app.route('/')
def admin_panel():
    return render_template('admin.html')

@app.route('/create', methods=['POST'])
def create_memory():
    page_id = str(uuid.uuid4())[:8]
    
    bg_type = request.form.get('bg_type', 'color') # نوع الخلفية (لون أم صورة)
    bg_color = request.form.get('bg_color', '#fff5f5')
    
    # رفع صورة الخلفية إذا تم اختيار رفع صورة
    bg_image_url = None
    if bg_type == 'image':
        bg_file = request.files.get('bg_image')
        if bg_file and bg_file.filename != '':
            bg_filename = f"bg_{page_id}_{bg_file.filename}"
            bg_file.save(os.path.join(app.config['UPLOAD_FOLDER'], bg_filename))
            bg_image_url = f"/static/uploads/{bg_filename}"

    # رفع الأغنية
    song_file = request.files.get('song')
    song_path = None
    if song_file and song_file.filename != '':
        song_filename = f"{page_id}_{song_file.filename}"
        song_file.save(os.path.join(app.config['UPLOAD_FOLDER'], song_filename))
        song_path = f"/static/uploads/{song_filename}"

    # رفع الميديا (صور أو فيديوهات) والنصوص
    media_files = request.files.getlist('media')
    texts = request.form.getlist('texts')
    
    moments = []
    for i, file in enumerate(media_files):
        if file and file.filename != '':
            filename = f"{page_id}_{i}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # تحديد نوع الملف (صورة أم فيديو)
            ext = file.filename.split('.')[-1].lower()
            is_video = ext in ['mp4', 'webm', 'ogg', 'mov']
            
            media_url = f"/static/uploads/{filename}"
            text = texts[i] if i < len(texts) else ""
            moments.append({
                "url": media_url, 
                "is_video": is_video, 
                "text": text
            })

    database[page_id] = {
        "bg_type": bg_type,
        "bg_color": bg_color,
        "bg_image_url": bg_image_url,
        "song_url": song_path,
        "moments": moments
    }

    generate_qr(page_id)
    return redirect(url_for('show_result', page_id=page_id))

@app.route('/result/<page_id>')
def show_result(page_id):
    return f'''
    <div style="text-align:center; font-family:sans-serif; padding:50px;">
        <h2>✅ تم إنشاء الصفحة بنجاح!</h2>
        <p><b>رابط الصفحة:</b> <a href="/p/{page_id}" target="_blank">اضغط هنا لمعاينة الصفحة</a></p>
        <img src="/static/qrcodes/{page_id}.png" style="width:200px; border:1px solid #ccc; padding:10px;"><br><br>
        <a href="/">+ إنشاء صفحة عميل جديد</a>
    </div>
    '''

@app.route('/p/<page_id>')
def show_couple_page(page_id):
    data = database.get(page_id)
    if not data:
        return "الصفحة غير موجودة", 404
    return render_template('couple.html', data=data)

def generate_qr(page_id):
    # بيجيب رابط الموقع الأونلاين أوتوماتيك
    domain = request.host_url.rstrip('/')
    target_url = f"{domain}/p/{page_id}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(app.config['QR_FOLDER'], f"{page_id}.png"))

if __name__ == '__main__':
    app.run(debug=True)