import os
import cv2
import numpy as np
import hashlib
from flask import Flask, render_template, request, send_file, url_for, flash, redirect, session

UPLOAD_FOLDER = 'uploads'
WATERMARK_STRENGTH = 10

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]KTPSEAL/'

def generate_pixel_indices(secret_key, num_pixels_to_change, max_index):
    hashed_key = hashlib.sha256(secret_key.encode()).hexdigest()
    seed = int(hashed_key, 16) % (2**32)
    np.random.seed(seed)
    num_to_select = min(num_pixels_to_change, max_index + 1)
    if num_to_select <= 0:
        return np.array([], dtype=int)
    indices = np.random.choice(max_index + 1, size=num_to_select, replace=False)
    return sorted(indices)

def embed_simple_watermark(image_path, secret_key, output_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            flash(f"Error [Embed]: Tidak dapat membaca gambar dari {image_path}", "danger")
            return False
        
        img_flat = img.flatten()
        total_pixels = len(img_flat)
        num_pixels_to_change = max(1, total_pixels // 100)

        pixel_indices_to_change = generate_pixel_indices(secret_key, num_pixels_to_change, total_pixels - 1)
        
        if len(pixel_indices_to_change) == 0:
            flash("Error [Embed]: Tidak ada piksel yang bisa diubah (gambar terlalu kecil atau masalah lain).", "danger")
            return False

        watermarked_img_flat = np.array(img_flat, dtype=np.int16)
        
        print(f"\n--- DEBUG EMBED (Spasial Minimalis) ---")
        print(f"Kunci: {secret_key}, Kekuatan: {WATERMARK_STRENGTH}")
        print(f"Jumlah piksel diubah: {len(pixel_indices_to_change)}")
        
        for i, index in enumerate(pixel_indices_to_change):
            original_value = watermarked_img_flat[index]
            if i % 2 == 0:
                watermarked_img_flat[index] += WATERMARK_STRENGTH
            else:
                watermarked_img_flat[index] -= WATERMARK_STRENGTH
        
        watermarked_img_flat_clipped = np.clip(watermarked_img_flat, 0, 255).astype(np.uint8)
        watermarked_img = watermarked_img_flat_clipped.reshape(img.shape)

        print(f"Output ke: {output_path}")
        print(f"--- AKHIR DEBUG EMBED ---\n")
        cv2.imwrite(output_path, watermarked_img)
        return True
    except Exception as e:
        flash(f"Error saat menyisipkan watermark spasial: {e}", "danger")
        print(f"Error Exception di embed_simple_watermark: {e}")
        return False

def detect_simple_watermark(image_path, secret_key):
    try:
        img_to_check = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img_to_check is None:
            print(f"Error [Detect]: Tidak dapat membaca gambar dari {image_path}")
            return None, 0.0

        img_flat_check = img_to_check.flatten()
        total_pixels = len(img_flat_check)
        num_pixels_to_change = max(1, total_pixels // 100)

        pixel_indices_to_check = generate_pixel_indices(secret_key, num_pixels_to_change, total_pixels - 1)
        
        if len(pixel_indices_to_check) == 0:
            print("Error [Detect]: Tidak ada piksel yang bisa dicek (gambar terlalu kecil atau masalah lain).")
            return None, 0.0

        spatial_watermark_signal_ref = np.zeros(total_pixels, dtype=np.float64)
        for i, index in enumerate(pixel_indices_to_check):
            if i % 2 == 0:
                spatial_watermark_signal_ref[index] = WATERMARK_STRENGTH
            else:
                spatial_watermark_signal_ref[index] = -WATERMARK_STRENGTH
        
        extracted_pixel_values_at_indices = np.array(img_flat_check[pixel_indices_to_check], dtype=np.float64)
        expected_watermark_pattern_at_indices = np.array(spatial_watermark_signal_ref[pixel_indices_to_check], dtype=np.float64)

        print(f"\n--- DEBUG DETECT (Spasial Minimalis) ---")
        print(f"Kunci: {secret_key}, Kekuatan Cek: {WATERMARK_STRENGTH}")
        print(f"Jumlah piksel dicek: {len(pixel_indices_to_check)}")
        if len(pixel_indices_to_check) > 0:
            print(f"Pola W spasial diharapkan (5 awal di indeks): {expected_watermark_pattern_at_indices[:5]}")
            print(f"Piksel diekstrak dari gambar (5 awal di indeks): {extracted_pixel_values_at_indices[:5]}")

        correlation = 0.0
        epsilon = 1e-10
        if len(expected_watermark_pattern_at_indices) > 1 and \
           (np.std(extracted_pixel_values_at_indices) > epsilon and np.std(expected_watermark_pattern_at_indices) > epsilon) :
            correlation = np.corrcoef(extracted_pixel_values_at_indices, expected_watermark_pattern_at_indices)[0, 1]
        elif len(expected_watermark_pattern_at_indices) > 0 :
            if np.allclose(extracted_pixel_values_at_indices, expected_watermark_pattern_at_indices):
                correlation = 1.0
            print(f"Peringatan [Detect]: Varians sangat kecil, korelasi mungkin tidak akurat.")

        print(f"Skor Korelasi (Piksel vs Pola Spasial): {correlation:.4f}")
        print(f"--- AKHIR DEBUG DETECT ---\n")
        
        if np.isnan(correlation): correlation = 0.0
        return True, correlation
    except Exception as e:
        print(f"Error saat mendeteksi watermark spasial: {e}")
        return None, 0.0

@app.route('/')
def index():
    active_form = request.args.get('active_form', 'embed')
    return render_template('index.html', active_form=active_form)

@app.route('/embed', methods=['POST'])
def handle_embed():
    if 'original_image' not in request.files or 'secret_key' not in request.form:
        flash("Form tidak lengkap! Pastikan gambar dan kunci rahasia diisi.", "danger")
        return redirect(url_for('index', active_form='embed'))
    
    file = request.files['original_image']
    key = request.form['secret_key']

    if file.filename == '':
        flash("Tidak ada file gambar dipilih!", "danger")
        return redirect(url_for('index', active_form='embed'))
    if not key:
        flash("Kunci rahasia tidak boleh kosong!", "danger")
        return redirect(url_for('index', active_form='embed'))

    if file:
        filename = file.filename
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(original_path)
        
        watermarked_filename = "watermarked_" + filename
        watermarked_path = os.path.join(app.config['UPLOAD_FOLDER'], watermarked_filename)
        
        success = embed_simple_watermark(original_path, key, watermarked_path)
        
        if success:
            flash("Watermark berhasil disisipkan! File akan diunduh.", "success")
            try:
                return send_file(watermarked_path, as_attachment=True)
            except Exception as e:
                flash(f"Gagal mengirim file: {e}", "danger")
                return redirect(url_for('index', active_form='embed'))
        else:
            if not any(True for _ in session.get('_flashes', [])):
                 flash("Gagal menyisipkan watermark ke gambar.", "danger")
            return redirect(url_for('index', active_form='embed'))
            
    return redirect(url_for('index', active_form='embed'))

@app.route('/detect', methods=['POST'])
def handle_detect():
    if 'image_to_check' not in request.files or 'secret_key' not in request.form:
        flash("Form tidak lengkap! Pastikan gambar dan kunci rahasia diisi.", "danger")
        return redirect(url_for('index', active_form='detect'))
        
    file = request.files['image_to_check']
    key = request.form['secret_key']

    if file.filename == '':
        flash("Tidak ada file gambar dipilih!", "danger")
        return redirect(url_for('index', active_form='detect'))
    if not key:
        flash("Kunci rahasia tidak boleh kosong!", "danger")
        return redirect(url_for('index', active_form='detect'))

    if file:
        filename = file.filename
        check_path = os.path.join(app.config['UPLOAD_FOLDER'], "check_" + filename)
        file.save(check_path)
        
        detected_status, correlation_score = detect_simple_watermark(check_path, key)
        
        session['detection_result'] = f"Skor Korelasi (Spasial): {correlation_score:.4f}."
        THRESHOLD = 0.1 
        if detected_status and correlation_score > THRESHOLD:
            session['detection_message'] = "Watermark (Spasial) TERDETEKSI!"
            session['detection_category'] = "success"
        else:
            session['detection_message'] = "Watermark (Spasial) TIDAK TERDETEKSI (atau kunci salah)."
            session['detection_category'] = "info"
        
        return redirect(url_for('index', active_form='detect'))
            
    return redirect(url_for('index', active_form='detect'))

if __name__ == '__main__':
   if not os.path.exists(UPLOAD_FOLDER):
       os.makedirs(UPLOAD_FOLDER)
       print(f"Folder '{UPLOAD_FOLDER}' dibuat.")
   app.run(debug=True)