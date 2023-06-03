
import re  
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import datetime

app = Flask(__name__) 

app.secret_key = 'abcdefgh'
  
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'cs353hw4db'
  
mysql = MySQL(app)  

@app.route('/')

@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = % s AND password = % s', (username, password, ))
        user = cursor.fetchone()
        if user:              
            session['loggedin'] = True
            session['userid'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return redirect(url_for('tasks'))
        else:
            message = 'Please enter correct email / password !'
    return render_template('login.html', message = message)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    session.pop('email', None)
    return redirect(url_for('login'))



@app.route('/register', methods =['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            message = 'Choose a different username!'
  
        elif not username or not password or not email:
            message = 'Please fill out the form!'

        else:
            cursor.execute('INSERT INTO User (id, username, email, password) VALUES (NULL, % s, % s, % s)', (username, email, password,))
            mysql.connection.commit()
            message = 'User successfully created!'

    elif request.method == 'POST':

        message = 'Please fill all the fields!'
    return render_template('register.html', message = message)

@app.route('/tasks', methods =['GET', 'POST'])
def tasks():
    userid = session['userid']
    print(f"User ID: {userid}")  # add this line to print the user_id to the console

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT * FROM Task WHERE user_id = %s ", (userid,))
    tasks = cur.fetchall()

    return render_template('tasks.html', tasks=tasks, userid = userid)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    # check if the user is logged in
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    # get the user_id from the logged in user
    userid = session.get('userid', None)

    # get the task from the database
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM Task WHERE id = %s AND user_id = %s", (task_id, userid, ))
    task = cur.fetchone()

    # check if the task exists and the user owns the task
    if not task:
        flash("Task not found!")
        return redirect(url_for('tasks'), task=task)

    if request.method == 'POST':
        # update the task in the database
        title = request.form['title']
        description = request.form['description']
        deadline = datetime.datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
        task_type = request.form['task_type']
        cur.execute("UPDATE Task SET title = %s, description = %s, deadline = %s, task_type = %s WHERE id = %s AND user_id = %s",
                    (title, description, deadline, task_type, task_id, userid))
        mysql.connection.commit()

        flash("Task updated successfully!")
        return redirect(url_for('tasks'))



@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    # check if the user is logged in
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    # get the user_id from the logged in user
    userid = session.get('userid', None)

    # delete the task from the database
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Task WHERE id = %s AND user_id = %s", (task_id, userid))
    mysql.connection.commit()

    flash("Task deleted successfully!")
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:id>/done', methods=['POST'])
def mark_task_done(id):
    # get the user_id from the logged in user
    userid = session.get('userid', None)

    # update the task status in the database
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("UPDATE Task SET status = 'Done', done_time = %s WHERE id = %s AND user_id = %s", (datetime.datetime.now(), id, userid))
    mysql.connection.commit()

    # redirect to the tasks page
    return redirect(url_for('tasks'))

@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form['description']
    deadline = datetime.datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
    task_type = request.form['task_type']

    # get the user_id from the logged in user
    userid = session.get('userid', None)
    # Create a new task in the database
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("INSERT INTO Task (id, title, description, status, deadline, creation_time, done_time, user_id, task_type) VALUES (NULL, %s, %s, %s, %s, %s, NULL, %s, %s)",
                (title, description, 'Todo', deadline, datetime.datetime.now(), userid, task_type))
    mysql.connection.commit()

    flash("Task added successfully!")
    return redirect(url_for('tasks'))

@app.route('/tasks', methods=['POST'])
def create_task():
    message =""
    if request.method == 'POST' and 'title' in request.form and 'description' in request.form and 'deadline' in request.form and 'task_type' in request.form:
        title = request.form['title']
        description = request.form['description']
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M:%S')
        task_type = request.form['task_type']

        # get the user_id from the logged in user
        userid = session.get('userid', None)
        # Create a new task in the database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("INSERT INTO Task (id, title, description, status, deadline, creation_time, done_time, userid, task_type) VALUES (NULL, %s, %s, %s, %s, %s, NULL, %s, %s)",
                    (title, description, 'todo', deadline, datetime.datetime.now(), userid, task_type))
        mysql.connection.commit()

        # Return a response
        
        message: 'Task created successfully.'
    
        flash("Task created successfully!")
    elif request.method == 'POST':
        message = 'Please fill all the fields!'
    return render_template('tasks.html', message= message)

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    # connect to the database
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    userid = session.get('userid', None)

    # query 1: list the title and latency of the tasks that were completed after their deadlines
    cur.execute('''SELECT title, done_time - deadline as latency
                 FROM Task WHERE status = 'Done' AND done_time > deadline AND user_id = %s''',
              (userid,))
    results1 = cur.fetchall()

    # query 2: give the average task completion time of the user
    cur.execute('''SELECT AVG(done_time - creation_time) as average
                 FROM Task WHERE status = 'Done' AND user_id = %s''',
              (userid,))
    results2 = cur.fetchone()

    # query 3: list the number of the completed tasks per task type, in descending order
    cur.execute('''SELECT task_type, COUNT(*) as num_completed
             FROM Task WHERE status = 'Done' AND user_id = %s
             GROUP BY task_type
             ORDER BY num_completed DESC''',  
          (userid,))
    results3 = cur.fetchall()

    # query 4: list the title and deadline of uncompleted tasks in increasing order of deadlines
    cur.execute('''SELECT title, deadline
                 FROM Task WHERE status = 'Todo' AND user_id = %s
                 ORDER BY deadline ASC''',
              (userid,))
    results4 = cur.fetchall()

    # query 5: list the title and task completion time of the top 2 completed tasks that took the most time
    cur.execute('''SELECT title, done_time - creation_time as completion_time
                 FROM Task WHERE status = 'Done' AND user_id = %s
                 ORDER BY completion_time DESC
                 LIMIT 2''',
              (userid,))
    results5 = cur.fetchall()

    cur.close()
    
    return render_template('analysis.html', results1=results1, results2=results2, results3=results3, results4=results4, results5=results5)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
