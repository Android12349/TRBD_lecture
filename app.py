from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
from wordcloud import WordCloud
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Настройка LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Загружаем данные Titanic из CSV
df = pd.read_csv('data/titanic.csv')

# Модель пользователя для простоты
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Страница авторизации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'trbd':
            user = User(id=username)
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Неверные данные для входа")
    
    return render_template('login.html')

# Выход из аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Главная страница
@app.route('/')
@login_required
def home():
    return render_template('home.html')

# Страница с таблицей данных
@app.route('/table')
@login_required
def table():
    columns = df.columns.tolist()
    data = df.to_dict(orient='records')  
    return render_template('table.html', columns=columns, data=data)

# Данные для линейного графика: распределение возраста
@app.route('/data/line_chart')
@login_required
def line_chart_data():
    age_distribution = df['age'].dropna().value_counts().sort_index()
    data = {'labels': age_distribution.index.tolist(), 'values': age_distribution.values.tolist()}
    return jsonify(data)

# Страница с линейным графиком
@app.route('/line_chart')
@login_required
def line_chart():
    return render_template('line_chart.html')

# Данные для круговой диаграммы: распределение по полу
@app.route('/data/pie_chart')
@login_required
def pie_chart_data():
    gender_distribution = df['sex'].value_counts()
    data = {'labels': gender_distribution.index.tolist(), 'values': gender_distribution.values.tolist()}
    return jsonify(data)

# Страница с круговой диаграммой
@app.route('/pie_chart')
@login_required
def pie_chart():
    return render_template('pie_chart.html')

# Данные для тепловой карты: выживаемость в зависимости от класса и пола
@app.route('/data/heatmap')
@login_required
def heatmap_data():
    # Преобразуем данные для тепловой карты
    heatmap_data = df.pivot_table(index='pclass', columns='sex', values='survived', aggfunc='mean').fillna(0)
    
    heatmap_values = heatmap_data.values.tolist()  # Значения для тепловой карты
    x_labels = heatmap_data.columns.tolist()       # Метки по оси X (пол)
    y_labels = heatmap_data.index.tolist()         # Метки по оси Y (класс)

    return jsonify({"z": heatmap_values, "x": x_labels, "y": y_labels})


# Страница с тепловой картой
@app.route('/heatmap')
@login_required
def heatmap():
    return render_template('heatmap.html')

# Данные для диаграммы Санки
@app.route('/data/sankey')
@login_required
def sankey_data():
    gender_class_survival = df.groupby(['sex', 'pclass', 'survived']).size().reset_index(name='count')
    data = {
        'labels': ["Male", "Female", "1st Class", "2nd Class", "3rd Class", "Survived", "Died"],
        'source': [0, 1, 0, 1, 0, 1, 2, 3, 4, 2, 3, 4],
        'target': [2, 2, 3, 3, 4, 4, 5, 5, 5, 6, 6, 6],
        'values': gender_class_survival['count'].tolist()
    }
    return jsonify(data)

# Страница с диаграммой Санки
@app.route('/sankey')
@login_required
def sankey():
    return render_template('sankey.html')

@app.route('/data/map')
def map_data():
    # Подсчёт количества пассажиров по порту посадки
    port_counts = df['embarked'].value_counts().to_dict()

    # Координаты портов посадки
    port_locations = {
        'C': {'name': 'Cherbourg', 'coords': [49.6333, -1.6167]},
        'Q': {'name': 'Queenstown', 'coords': [51.8498, -8.2948]},
        'S': {'name': 'Southampton', 'coords': [50.9097, -1.4043]}
    }

    # Создаем данные для передачи на карту
    map_data = []
    for port, count in port_counts.items():
        if port in port_locations:
            map_data.append({
                'name': port_locations[port]['name'],
                'coords': port_locations[port]['coords'],
                'count': count
            })

    return jsonify(map_data)

@app.route('/map')
@login_required
def map():
    return render_template('map.html')

# Маршрут для получения изображения облака слов
@app.route('/wordcloud_image')
@login_required
def wordcloud_image():
    text = " ".join(df['name'].fillna('').tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    return jsonify({'img_data': img_data})

# Маршрут для страницы с облаком слов
@app.route('/wordcloud')
@login_required
def wordcloud():
    return render_template('wordcloud.html')

if __name__ == '__main__':
    app.run(debug=True)
