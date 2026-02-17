import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from dotenv import load_dotenv
from models import db, Case
import io

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Создание таблиц при первом запуске (в production лучше использовать миграции)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Главная страница со ссылками на основные разделы"""
    return render_template('index.html')

@app.route('/cases')
def list_cases():
    """Список всех кейсов с возможностью фильтрации по сложности"""
    difficulty = request.args.get('difficulty')
    query = Case.query
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    cases = query.order_by(Case.created_at.desc()).all()
    return render_template('list_cases.html', cases=cases, selected_difficulty=difficulty)

@app.route('/cases/add', methods=['GET', 'POST'])
def add_case():
    """Добавление нового кейса (файл теперь необязателен)"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip() or None
        description = request.form.get('description', '').strip()
        difficulty = request.form.get('difficulty')
        file = request.files.get('excalidraw_file')

        # Проверка обязательных полей
        if not description or not difficulty:
            flash('Пожалуйста, заполните все обязательные поля.', 'danger')
            return redirect(url_for('add_case'))

        # Если файл загружен, проверяем его расширение и содержимое
        content = None
        if file and file.filename:
            if not file.filename.endswith('.excalidraw'):
                flash('Файл должен иметь расширение .excalidraw', 'danger')
                return redirect(url_for('add_case'))
            try:
                content = file.read().decode('utf-8')
                # Проверяем, что это валидный JSON
                json.loads(content)
            except (UnicodeDecodeError, json.JSONDecodeError):
                flash('Файл должен быть корректным JSON (формат .excalidraw)', 'danger')
                return redirect(url_for('add_case'))

        # Создаём запись в БД (content может быть None)
        case = Case(
            title=title,
            description=description,
            difficulty=difficulty,
            excalidraw_content=content
        )
        db.session.add(case)
        db.session.commit()

        flash('Кейс успешно добавлен!', 'success')
        return redirect(url_for('list_cases'))

    return render_template('add_case.html')

@app.route('/cases/<int:case_id>')
def view_case(case_id):
    """Просмотр деталей кейса и содержимого Excalidraw"""
    case = Case.query.get_or_404(case_id)
    return render_template('case_detail.html', case=case)

@app.route('/cases/<int:case_id>/download')
def download_case(case_id):
    """Скачивание файла .excalidraw для кейса (если он есть)"""
    case = Case.query.get_or_404(case_id)
    if not case.excalidraw_content:
        abort(404, description="Файл не прикреплён к этому кейсу.")
    
    file_data = io.BytesIO(case.excalidraw_content.encode('utf-8'))
    filename = f"case_{case_id}.excalidraw"
    if case.title:
        filename = f"{case.title}.excalidraw".replace(' ', '_')
    return send_file(
        file_data,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )

@app.route('/cases/random')
def random_case():
    """Получение случайного кейса по параметрам (сложность)"""
    difficulty = request.args.get('difficulty')

    # Если сложность указана и не пустая – фильтруем, иначе – все кейсы
    if difficulty:
        case = Case.query.filter_by(difficulty=difficulty).order_by(db.func.random()).first()
    else:
        case = Case.query.order_by(db.func.random()).first()

    print(case)
    # Если кейс не найден (например, нет кейсов с такой сложностью)
    if difficulty and not case:
        flash('Кейс не найден по заданным критериям', 'warning')
        return redirect(url_for('random_case'))

    return render_template('random_case.html', case=case, selected_difficulty=difficulty)

if __name__ == '__main__':
    app.run(debug=True)