
# from flask import Flask
# from config import SECRET_KEY
# from models.database import init_db
# from routes.main import main_bp
# from routes.admin import admin_bp

# app = Flask(__name__)
# app.config['SECRET_KEY'] = SECRET_KEY

# init_db()

# app.register_blueprint(main_bp)
# app.register_blueprint(admin_bp)

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)




from flask import Flask, render_template, request
from config import SECRET_KEY, GYM_PHONE, GYM_WHATSAPP, GYM_INSTAGRAM, RAZORPAY_KEY_ID
from models.database import init_db
from routes.main import main_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

init_db()

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

@app.context_processor
def inject_gym_info():
    return dict(
        gym_phone=GYM_PHONE,
        gym_whatsapp=GYM_WHATSAPP,
        gym_instagram=GYM_INSTAGRAM,
        razorpay_key_id=RAZORPAY_KEY_ID
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)



# ─── Turbo Speed Optimization ───────────────────────────────────
@app.after_request
def add_header(response):
    # Static files (CSS, JS, Images) ko 1 din ke liye cache kar lega browser mein
    if 'static' in request.path:
        response.headers['Cache-Control'] = 'public, max-age=86400'
    else:
        # HTML pages ko 10 seconds ke liye cache karega
        response.headers['Cache-Control'] = 'public, max-age=10'
    return response
