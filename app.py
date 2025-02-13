from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# configure sqlalchmey to tell flask where the databse is present
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'

# this is optional it is to avoid warnings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creates a "database manager" object tied to your Flask app.
# This handles connections, queries, and transactions automatically.
db = SQLAlchemy(app)

class Todo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  task = db.Column(db.String(80), unique=True, nullable=False)
  # __repr__(self) helps debugging. On return of type will show <Todo Learn HTMX> instead of <Todo object at 0x7f8c3d4a7d60>
  def __repr__(self):
    return f"<Todo {self.task}>"
  

# Creates the actual database file and tables based on your models. 
# Run this once when setting up your app. 
# Use app.app_context() because Flask needs to know which app to work with.
with app.app_context():
  db.create_all()


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
def home():
  if request.method == 'POST':
      TASK = request.form.get('task', '').strip()  # Removes extra spaces
      if not TASK:
          return "Task cannot be empty", 400
      
      new_todo = Todo(task=TASK)
      try:
          db.session.add(new_todo)
          db.session.commit()
      except Exception as e:
          db.session.rollback() # prevents partial commits
          return f"Error: {e}", 500
      
      # Return only task list for HTMX (no redirect)
      if request.headers.get("HX-Request"):
          tasks = Todo.query.order_by(Todo.id.desc()).all()
          return render_template('__partials/task_list.html', tasks=tasks)
      
      # Only redirect if NOT an HTMX request
      return redirect(url_for('home'))

  # Fetch all tasks for initial page load or page refresh
  tasks = Todo.query.order_by(Todo.id.desc()).all()
  return render_template('index.html', name="Jakob Vargis", app_name="Todo Tasks", tasks=tasks)


@app.route('/edit/<int:task_id>', methods=['GET'])
def task_edit(task_id):
   if request.method == 'GET':
        TASK = Todo.query.get_or_404(task_id)
        return render_template('__partials/edit_task_list.html', task=TASK)


@app.route('/update/<int:task_id>', methods=['POST'])
def task_update(task_id):
   if request.method == 'POST':
      TASK = Todo.query.get_or_404(task_id)
      new_task_value = request.form.get('task', '').strip()
      if not new_task_value:
         return "Task cannot be empty", 400
      
      TASK.task = new_task_value
      try:
         db.session.commit()
      except Exception as e:
         db.session.rollback()
         return f"Error: {e}", 500
      return render_template('__partials/task_item.html', task=TASK)


@app.route('/cancel/<int:task_id>', methods=['GET'])
def cancel_edit(task_id):
   if request.method == 'GET':
      TASK = Todo.query.get_or_404(task_id)
      return render_template('__partials/task_item.html', task=TASK)


@app.route('/delete/<int:task_id>', methods=['DELETE'])
def task_delete(task_id):
    TASK = Todo.query.get_or_404(task_id)
    try:
        db.session.delete(TASK)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}", 500

    # Return an empty response to let HTMX remove the task from the UI
    return "", 200


if __name__ == '__main__':
   app.run('0.0.0.0', debug=True)