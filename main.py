from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user, logout_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'lol'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Пожалуйста, авторизуйтесь, чтобы получить доступ к этой странице."
login_manager.login_message_category = "danger"


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    cards = db.relationship('Card', backref='author', lazy=True)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subtitle = db.Column(db.String(150), nullable=False)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

@app.route('/home')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('home.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user_exists = db.session.query(Users).filter_by(username=username).first()
        if user_exists:
            flash('Пользователь с таким именем уже существует.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = Users(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Успешная регистрация! Теперь Вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.session.query(Users).filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Неверное имя пользователя или пароль!', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
@login_required
def index():
    cards = db.session.query(Card).filter_by(user_id=current_user.id).all()
    return render_template('index.html', cards=cards)

@app.route('/card/<int:id>')
@login_required
def card(id):
    card_item = db.session.get(Card, id)
    if not card_item or card_item.user_id != current_user.id:
        flash('Запись не найдена.', 'danger')
        return redirect(url_for('index'))
    return render_template('card.html', card=card_item)

@app.route('/create')
@login_required
def create():
    return render_template('create.html')

@app.route('/form_create', methods=["GET", "POST"])
@login_required
def form_create():
    if request.method == "POST":
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        text = request.form.get('text')

        if not title or not subtitle or not text:
            flash('Все поля должны быть заполнены!', 'danger')
            return redirect(url_for('create'))

        new_card = Card(title=title, subtitle=subtitle, text=text, user_id=current_user.id)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('index'))

    return redirect(url_for('create'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_card(id):
    card_item = db.session.get(Card, id)
    if not card_item or card_item.user_id != current_user.id:
        flash('Запись не найдена.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        card_item.title = request.form.get('title')
        card_item.subtitle = request.form.get('subtitle')
        card_item.text = request.form.get('text')
        db.session.commit()
        flash('Запись успешно обновлена!', 'success')
        return redirect(url_for('index'))
        
    return render_template('edit.html', card=card_item)

@app.route('/delete_card/<int:id>')
@login_required
def delete_card(id):
    card_item = db.session.get(Card, id)
    if card_item and card_item.user_id == current_user.id:
        db.session.delete(card_item)
        db.session.commit()
        flash('Запись успешно удалена!', 'success')
    else:
        flash('Запись не найдена.', 'danger')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)

