import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import sys

dbConnectionCount=0
totalPostCount=0
# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global dbConnectionCount
    dbConnectionCount+=1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post
def get_total_postcount():
    connection = get_db_connection()
    global totalPostCount
    count = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    totalPostCount=len(count)

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
get_total_postcount()

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('The post id = %d does not exist ',post_id)
      return render_template('404.html'), 404
    else:
      app.logger.info('Article " %s " retrieved',post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About page retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            global totalPostCount
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            totalPostCount+=1
            app.logger.info('A new article is created with the title: %s',title)
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthcheck():
    app.logger.info('healthz endpoint was reached')
    try:
        get_total_postcount()
    except Exception:
        return app.response_class(
                response=json.dumps({"result":"Error - unhealthy"}),
                status=200,
                mimetype='application/json'
        )
    return app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

@app.route('/metrics')
def metricscheck():
    response = app.response_class(
            response=json.dumps({"db_connection_count": dbConnectionCount, "post_count": totalPostCount}),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('metrics endpoint was reached')
    return response

# start the application on port 3111
if __name__ == "__main__":
   stdout_handler = logging.StreamHandler(sys.stdout)
   stdout_handler.setLevel(logging.DEBUG)
   stderr_handler = logging.StreamHandler(sys.stderr)
   stderr_handler.setLevel(logging.ERROR)
   dual_handlers = [stdout_handler, stderr_handler]
   logging.basicConfig(level=logging.DEBUG,format='%(levelname)s: %(asctime)s , %(message)s',handlers=dual_handlers)
   app.run(host='0.0.0.0', port='3111')