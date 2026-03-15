from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'avita-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///avita.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# SocketIO инициализируется только если не запущено через WSGI
# Для хостинга можно отключить, установив переменную окружения DISABLE_SOCKETIO=1
if os.environ.get('DISABLE_SOCKETIO') != '1':
    try:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    except:
        socketio = None
else:
    socketio = None

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(256), default='default_avatar.png')
    role = db.Column(db.String(20), default='buyer')  # buyer, master, admin
    is_verified = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(100))
    about = db.Column(db.Text)
    
    ads = db.relationship('Ad', backref='author', lazy=True)
    vacancies = db.relationship('Vacancy', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    ads = db.relationship('Ad', backref='category', lazy=True)

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float)
    price_negotiable = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(100))
    images = db.Column(db.Text)  # JSON string of image paths
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, sold, rejected
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)

class Vacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary_from = db.Column(db.Float)
    salary_to = db.Column(db.Float)
    experience = db.Column(db.String(50))
    schedule = db.Column(db.String(50))
    location = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ad_id = db.Column(db.Integer, db.ForeignKey('ad.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    ad = db.relationship('Ad')
    messages = db.relationship('Message', backref='chat', lazy=True, order_by='Message.created_at')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User')

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ad_id = db.Column(db.Integer, db.ForeignKey('ad.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ad_id = db.Column(db.Integer, db.ForeignKey('ad.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reason = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    ad = db.relationship('Ad')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Categories data
CATEGORIES = {
    'transport': {
        'name': 'Транспорт',
        'icon': 'fa-car',
        'children': ['Автомобили', 'Новые авто', 'Аренда авто', 'Запчасти и аксессуары', 
                    'Грузовики и спецтехника', 'Аренда техники', 'Мотоциклы и мототехника', 'Водный транспорт']
    },
    'realestate': {
        'name': 'Недвижимость',
        'icon': 'fa-home',
        'children': ['Новостройки', 'Коммерческая', 'Покупка дома', 'Покупка квартиры', 
                    'Ипотека', 'Оценка квартиры', 'Аренда квартиры', 'Аренда дома']
    },
    'work': {
        'name': 'Работа',
        'icon': 'fa-briefcase',
        'children': ['Ищу работу', 'Ищу сотрудника']
    },
    'services': {
        'name': 'Услуги',
        'icon': 'fa-wrench',
        'children': ['Перевозки и доставка', 'Ремонт и отделка', 'Ремонт техники', 'Уборка',
                    'Оборудование, производство', 'Красота', 'Строительство', 'Деловые услуги',
                    'Обучение, курсы', 'Установка техники']
    },
    'personal': {
        'name': 'Личные вещи',
        'icon': 'fa-tshirt',
        'children': ['Женская одежда', 'Женская обувь', 'Мужская одежда', 'Мужская обувь',
                    'Детская одежда и обувь', 'Платья', 'Мужские футболки', 'Часы', 'Ювелирные изделия']
    },
    'home': {
        'name': 'Для дома и дачи',
        'icon': 'fa-couch',
        'children': ['Ремонт и стройка', 'Инструменты', 'Мебель и интерьер', 'Детская мебель',
                    'Кухонные гарнитуры', 'Предметы интерьера', 'Текстиль и ковры', 
                    'Товары для кухни', 'Растения']
    },
    'electronics': {
        'name': 'Электроника',
        'icon': 'fa-mobile-alt',
        'children': ['Телефоны', 'Бытовая техника', 'Ноутбуки', 'Настольные компьютеры',
                    'Телевизоры', 'Колонки', 'Комплектующие для ПК', 'Планшеты',
                    'Игровые приставки и аксессуары', 'Наушники', 'Музыкальные центры']
    },
    'hobby': {
        'name': 'Хобби и отдых',
        'icon': 'fa-bicycle',
        'children': ['Билеты и путешествия', 'Велосипеды', 'Книги и журналы', 'Коллекционирование',
                    'Музыкальные инструменты', 'Охота и рыбалка', 'Спорт и отдых']
    },
    'animals': {
        'name': 'Животные',
        'icon': 'fa-paw',
        'children': ['Собаки', 'Кошки', 'Птицы', 'Грызуны', 'Аквариум', 'Кролики',
                    'Рептилии', 'Фермерские животные', 'Зоотовары']
    },
    'business': {
        'name': 'Бизнес и оборудование',
        'icon': 'fa-industry',
        'children': ['Готовый бизнес', 'Оборудование для бизнеса', 'Франшизы']
    },
    'kids': {
        'name': 'Товары для детей',
        'icon': 'fa-baby',
        'children': ['Автомобильные кресла', 'Самокаты и велосипеды', 'Детская мебель',
                    'Детские коляски', 'Игрушки', 'Постельные принадлежности',
                    'Товары для кормления', 'Товары для купания', 'Товары для школы', 'Детская гигиена']
    },
    'beauty': {
        'name': 'Красота и здоровье',
        'icon': 'fa-spa',
        'children': ['Макияж и маникюр', 'Парфюмерия', 'Приборы и аксессуары',
                    'Уход и гигиена', 'Средства для волос', 'Медицинские изделия']
    }
}

def init_categories():
    if Category.query.count() == 0:
        for slug, data in CATEGORIES.items():
            parent = Category(name=data['name'], slug=slug, icon=data['icon'])
            db.session.add(parent)
            db.session.flush()
            
            for child_name in data['children']:
                child_slug = f"{slug}_{child_name.lower().replace(' ', '_').replace(',', '')}"
                child = Category(name=child_name, slug=child_slug, parent_id=parent.id)
                db.session.add(child)
        
        db.session.commit()

def create_admin():
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@avita.ru',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def index():
    categories = Category.query.filter_by(parent_id=None).all()
    featured_ads = Ad.query.filter_by(status='active').order_by(Ad.created_at.desc()).limit(12).all()
    return render_template('index.html', categories=categories, featured_ads=featured_ads)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        role = request.form.get('role', 'buyer')
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
            role=role if role in ['buyer', 'master'] else 'buyer'
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_banned:
                flash('Ваш аккаунт заблокирован', 'error')
                return redirect(url_for('login'))
            
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        
        flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user_ads = Ad.query.filter_by(user_id=current_user.id).order_by(Ad.created_at.desc()).all()
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_ads = [Ad.query.get(f.ad_id) for f in favorites]
    return render_template('profile.html', user_ads=user_ads, favorite_ads=favorite_ads)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.phone = request.form.get('phone')
        current_user.location = request.form.get('location')
        current_user.about = request.form.get('about')
        
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.avatar = filename
        
        db.session.commit()
        flash('Профиль обновлен', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    user_ads = Ad.query.filter_by(user_id=user_id, status='active').order_by(Ad.created_at.desc()).all()
    return render_template('user_profile.html', user=user, user_ads=user_ads)

@app.route('/category/<slug>')
def category(slug):
    cat = Category.query.filter_by(slug=slug).first_or_404()
    
    if cat.parent_id is None:
        # Main category - show all ads from subcategories
        subcategory_ids = [c.id for c in cat.children]
        subcategory_ids.append(cat.id)
        ads = Ad.query.filter(Ad.category_id.in_(subcategory_ids), Ad.status == 'active').order_by(Ad.created_at.desc()).all()
    else:
        ads = Ad.query.filter_by(category_id=cat.id, status='active').order_by(Ad.created_at.desc()).all()
    
    return render_template('category.html', category=cat, ads=ads)

@app.route('/ad/new', methods=['GET', 'POST'])
@login_required
def new_ad():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price')
        category_id = request.form.get('category_id')
        location = request.form.get('location')
        price_negotiable = request.form.get('price_negotiable') == 'on'
        
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files[:10]:  # Max 10 images
                if file and file.filename:
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    images.append(filename)
        
        ad = Ad(
            title=title,
            description=description,
            price=float(price) if price else None,
            price_negotiable=price_negotiable,
            location=location,
            images=','.join(images),
            category_id=category_id,
            user_id=current_user.id,
            status='active'  # Auto-approve for now
        )
        db.session.add(ad)
        db.session.commit()
        
        flash('Объявление создано!', 'success')
        return redirect(url_for('ad_detail', ad_id=ad.id))
    
    categories = Category.query.all()
    return render_template('new_ad.html', categories=categories)

@app.route('/ad/<int:ad_id>')
def ad_detail(ad_id):
    ad = Ad.query.get_or_404(ad_id)
    ad.views += 1
    db.session.commit()
    
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(user_id=current_user.id, ad_id=ad_id).first() is not None
    
    similar_ads = Ad.query.filter(Ad.category_id == ad.category_id, Ad.id != ad.id, Ad.status == 'active').limit(4).all()
    
    return render_template('ad_detail.html', ad=ad, is_favorite=is_favorite, similar_ads=similar_ads)

@app.route('/ad/<int:ad_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ad(ad_id):
    ad = Ad.query.get_or_404(ad_id)
    
    if ad.user_id != current_user.id and current_user.role != 'admin':
        flash('У вас нет прав для редактирования', 'error')
        return redirect(url_for('ad_detail', ad_id=ad_id))
    
    if request.method == 'POST':
        ad.title = request.form.get('title')
        ad.description = request.form.get('description')
        ad.price = float(request.form.get('price')) if request.form.get('price') else None
        ad.category_id = request.form.get('category_id')
        ad.location = request.form.get('location')
        ad.price_negotiable = request.form.get('price_negotiable') == 'on'
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            new_images = []
            for file in files[:10]:
                if file and file.filename:
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    new_images.append(filename)
            if new_images:
                ad.images = ','.join(new_images)
        
        db.session.commit()
        flash('Объявление обновлено', 'success')
        return redirect(url_for('ad_detail', ad_id=ad_id))
    
    categories = Category.query.all()
    return render_template('edit_ad.html', ad=ad, categories=categories)

@app.route('/ad/<int:ad_id>/delete', methods=['POST'])
@login_required
def delete_ad(ad_id):
    ad = Ad.query.get_or_404(ad_id)
    
    if ad.user_id != current_user.id and current_user.role != 'admin':
        flash('У вас нет прав для удаления', 'error')
        return redirect(url_for('ad_detail', ad_id=ad_id))
    
    db.session.delete(ad)
    db.session.commit()
    flash('Объявление удалено', 'success')
    return redirect(url_for('profile'))

@app.route('/ad/<int:ad_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(ad_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, ad_id=ad_id).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        favorite = Favorite(user_id=current_user.id, ad_id=ad_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'added'})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category_id = request.args.get('category')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    location = request.args.get('location')
    
    ads = Ad.query.filter(Ad.status == 'active')
    
    if query:
        ads = ads.filter(Ad.title.contains(query) | Ad.description.contains(query))
    
    if category_id:
        ads = ads.filter_by(category_id=category_id)
    
    if min_price:
        ads = ads.filter(Ad.price >= float(min_price))
    
    if max_price:
        ads = ads.filter(Ad.price <= float(max_price))
    
    if location:
        ads = ads.filter(Ad.location.contains(location))
    
    ads = ads.order_by(Ad.created_at.desc()).all()
    categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('search.html', ads=ads, query=query, categories=categories)

# Vacancy routes for Masters
@app.route('/vacancies')
def vacancies():
    all_vacancies = Vacancy.query.filter_by(status='active').order_by(Vacancy.created_at.desc()).all()
    return render_template('vacancies.html', vacancies=all_vacancies)

@app.route('/vacancy/new', methods=['GET', 'POST'])
@login_required
def new_vacancy():
    if current_user.role not in ['master', 'admin']:
        flash('Только мастера могут создавать вакансии', 'error')
        return redirect(url_for('vacancies'))
    
    if request.method == 'POST':
        vacancy = Vacancy(
            title=request.form.get('title'),
            description=request.form.get('description'),
            salary_from=float(request.form.get('salary_from')) if request.form.get('salary_from') else None,
            salary_to=float(request.form.get('salary_to')) if request.form.get('salary_to') else None,
            experience=request.form.get('experience'),
            schedule=request.form.get('schedule'),
            location=request.form.get('location'),
            company_name=request.form.get('company_name'),
            user_id=current_user.id,
            status='active'
        )
        db.session.add(vacancy)
        db.session.commit()
        
        flash('Вакансия создана!', 'success')
        return redirect(url_for('vacancy_detail', vacancy_id=vacancy.id))
    
    return render_template('new_vacancy.html')

@app.route('/vacancy/<int:vacancy_id>')
def vacancy_detail(vacancy_id):
    vacancy = Vacancy.query.get_or_404(vacancy_id)
    return render_template('vacancy_detail.html', vacancy=vacancy)

# Chat routes
@app.route('/messages')
@login_required
def messages():
    chats = Chat.query.filter((Chat.user1_id == current_user.id) | (Chat.user2_id == current_user.id)).all()
    return render_template('messages.html', chats=chats)

@app.route('/chat/<int:user_id>')
@app.route('/chat/<int:user_id>/<int:ad_id>')
@login_required
def chat(user_id, ad_id=None):
    if user_id == current_user.id:
        flash('Вы не можете написать себе', 'error')
        return redirect(url_for('messages'))
    
    other_user = User.query.get_or_404(user_id)
    
    # Find existing chat or create new
    existing_chat = Chat.query.filter(
        ((Chat.user1_id == current_user.id) & (Chat.user2_id == user_id)) |
        ((Chat.user1_id == user_id) & (Chat.user2_id == current_user.id))
    ).first()
    
    if not existing_chat:
        existing_chat = Chat(user1_id=current_user.id, user2_id=user_id, ad_id=ad_id)
        db.session.add(existing_chat)
        db.session.commit()
    
    # Mark messages as read
    Message.query.filter_by(chat_id=existing_chat.id, is_read=False).filter(Message.sender_id != current_user.id).update({'is_read': True})
    db.session.commit()
    
    return render_template('chat.html', chat=existing_chat, other_user=other_user)

@app.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    chat_id = data.get('chat_id')
    content = data.get('content')
    
    chat = Chat.query.get_or_404(chat_id)
    
    if current_user.id not in [chat.user1_id, chat.user2_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    message = Message(chat_id=chat_id, sender_id=current_user.id, content=content)
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'sender_id': message.sender_id,
        'created_at': message.created_at.strftime('%H:%M')
    })

@app.route('/api/chat/<int:chat_id>/messages')
@login_required
def get_chat_messages(chat_id):
    """Получение новых сообщений для polling (если SocketIO недоступен)"""
    after_id = request.args.get('after', 0, type=int)
    
    chat = Chat.query.get_or_404(chat_id)
    
    if current_user.id not in [chat.user1_id, chat.user2_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Получаем новые сообщения после указанного ID
    messages = Message.query.filter(
        Message.chat_id == chat_id,
        Message.id > after_id
    ).order_by(Message.created_at.asc()).all()
    
    return jsonify({
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender_id,
            'created_at': msg.created_at.strftime('%H:%M')
        } for msg in messages]
    })

# Socket.IO events (только если SocketIO активен)
if socketio:
    @socketio.on('join')
    def on_join(data):
        room = data['room']
        join_room(room)

    @socketio.on('leave')
    def on_leave(data):
        room = data['room']
        leave_room(room)

    @socketio.on('message')
    def handle_message(data):
        room = data['room']
        emit('message', data, room=room)

# Admin routes
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    stats = {
        'users': User.query.count(),
        'ads': Ad.query.count(),
        'pending_ads': Ad.query.filter_by(status='pending').count(),
        'vacancies': Vacancy.query.count(),
        'reports': Report.query.filter_by(status='pending').count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@login_required
def admin_ban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    
    return jsonify({'status': 'banned' if user.is_banned else 'unbanned'})

@app.route('/admin/user/<int:user_id>/role', methods=['POST'])
@login_required
def admin_change_role(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')
    
    if new_role in ['buyer', 'master', 'admin']:
        user.role = new_role
        db.session.commit()
        return jsonify({'status': 'success', 'role': new_role})
    
    return jsonify({'error': 'Invalid role'}), 400

@app.route('/admin/ads')
@login_required
def admin_ads():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    status = request.args.get('status', 'all')
    
    if status == 'all':
        ads = Ad.query.order_by(Ad.created_at.desc()).all()
    else:
        ads = Ad.query.filter_by(status=status).order_by(Ad.created_at.desc()).all()
    
    return render_template('admin/ads.html', ads=ads, current_status=status)

@app.route('/admin/ad/<int:ad_id>/status', methods=['POST'])
@login_required
def admin_ad_status(ad_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    ad = Ad.query.get_or_404(ad_id)
    new_status = request.json.get('status')
    
    if new_status in ['pending', 'active', 'rejected', 'sold']:
        ad.status = new_status
        db.session.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'Invalid status'}), 400

@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin/reports.html', reports=reports)

@app.route('/report', methods=['POST'])
@login_required
def create_report():
    ad_id = request.form.get('ad_id')
    reason = request.form.get('reason')
    description = request.form.get('description')
    
    report = Report(
        reporter_id=current_user.id,
        ad_id=ad_id,
        reason=reason,
        description=description
    )
    db.session.add(report)
    db.session.commit()
    
    flash('Жалоба отправлена', 'success')
    return redirect(url_for('ad_detail', ad_id=ad_id))

# API endpoints
@app.route('/api/categories')
def api_categories():
    categories = Category.query.filter_by(parent_id=None).all()
    result = []
    for cat in categories:
        result.append({
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'children': [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in cat.children]
        })
    return jsonify(result)

@app.route('/api/unread_messages')
@login_required
def unread_messages():
    count = Message.query.join(Chat).filter(
        ((Chat.user1_id == current_user.id) | (Chat.user2_id == current_user.id)),
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).count()
    return jsonify({'count': count})

if __name__ == '__main__':
    # Проверяем, запущено ли через Passenger (хостинг)
    # Если запускаем напрямую python app.py - это локальный запуск
    is_passenger = os.environ.get('PASSENGER_APP_ENV') is not None
    
    # Если запущено через Passenger - не запускаем сервер напрямую
    if is_passenger:
        print("=" * 60)
        print("⚠️  ВНИМАНИЕ: На хостинге Beget нельзя запускать сервер напрямую!")
        print("=" * 60)
        print("\nИспользуйте Passenger WSGI для запуска приложения.")
        print("Приложение уже настроено и работает через passenger_wsgi.py")
        print("\nДля проверки работы откройте сайт в браузере.")
        print("Для перезапуска используйте: touch tmp/restart.txt")
        print("\nИнициализация базы данных...")
        
        # Инициализируем БД, но не запускаем сервер
        with app.app_context():
            try:
                db.create_all()
                init_categories()
                create_admin()
                print("✅ База данных инициализирована успешно!")
                print("\n✅ Готово! Приложение работает через Passenger WSGI.")
            except Exception as e:
                print(f"ℹ️  База данных уже инициализирована или ошибка: {e}")
    else:
        # Локальный запуск для разработки
        print("🚀 Запуск в режиме разработки...")
        with app.app_context():
            db.create_all()
            init_categories()
            create_admin()
        
        if socketio:
            print("📡 SocketIO включен")
            socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
        else:
            print("🌐 Запуск Flask сервера...")
            app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
else:
    # Запуск через WSGI (для хостинга)
    # Инициализация базы данных при первом импорте
    with app.app_context():
        try:
            db.create_all()
            init_categories()
            create_admin()
        except Exception as e:
            # Если БД уже создана или есть другие ошибки, продолжаем
            pass
