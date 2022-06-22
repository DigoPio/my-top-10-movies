from crypt import methods
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from data_secret import DataSecret

secret = DataSecret()

API_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
API_DETAILS_URL = 'https://api.themoviedb.org/3/movie'
API_IMAGE_URL = 'https://image.tmdb.org/t/p/w300'
API_KEY = secret.api_key



app = Flask(__name__)
app.config['SECRET_KEY'] = secret.secret_key
Bootstrap(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(200), unique=False, nullable=True)
    rating = db.Column(db.Float, unique=False, nullable=True)
    ranking = db.Column(db.Integer, unique=True, nullable=True)
    review = db.Column(db.String(200), unique=False, nullable=True)
    img_url = db.Column(db.String(200), unique=False, nullable=False)

    def __repr__(self):
        return f'{self.title} - {self.year} - {self.ranking}'


db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating from 0 to 10')
    review = StringField('Your Review')
    submit = SubmitField('Done')

class FindMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')



@app.route("/")
def home():
    if os.path.isfile('movies.db'):
        all_movies = Movie.query.order_by(Movie.rating).all()
        total_movies = len(all_movies)
        for num in range(total_movies):
            all_movies[num].ranking = total_movies
            total_movies -= 1
        return render_template('index.html', movies=all_movies)
    return render_template("index.html")

@app.route('/edit', methods=['POST', 'GET'])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form )
    
@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(API_SEARCH_URL, params={'api_key': API_KEY, 'query': movie_title })
        data = response.json()['results']
        return render_template('select.html', options=data)
    return render_template('add.html', form=form)

@app.route('/find')
def find_movie():
    movie_api_id = request.args.get('id')
    print(movie_api_id)
    if movie_api_id:
        movie_api_url = f'{API_DETAILS_URL}/{movie_api_id}'
        response = requests.get(movie_api_url, params={'api_key': API_KEY})
        data = response.json()
        new_movie = Movie(
            title = data['title'],
            year = data['release_date'].split('-')[0],
            img_url = f"{API_IMAGE_URL}{data['poster_path']}",
            description = data['overview']
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('rate_movie', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
