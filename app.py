import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
USERS_DATABASE_URL = os.getenv('USERS_DATABASE_URL')
app.secret_key = os.getenv('FLASK_SECRET_KEY')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.DictCursor)
    return conn

def get_users_db_connection():
    conn = psycopg2.connect(USERS_DATABASE_URL, cursor_factory=psycopg2.extras.DictCursor)
    return conn

def format_datetime(value, format='%Y-%m-%d'):
    if value is None:
        return ""
    return value.strftime(format)

app.jinja_env.filters['datetime'] = format_datetime

    
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_users_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT "userId", "givenName" FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()


        if user:
            session['user_id'] = user['userId']
            session['name'] = user['givenName']
            print(session['user_id'])
            print(session['name'])
            return redirect(url_for('index'))  # Redirige a la página principal después del login
        else:
            flash('El email ingresado no existe.')
            return redirect(url_for('login'))  # Redirige de nuevo a la página de login
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/accounts')
@login_required
def accounts():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM accounts WHERE user_id = %s', (user_id,))
    account_data = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('accounts.html', accounts=account_data)

@app.route('/create_account', methods=['POST'])
@login_required
def create_account():
    user_id = session['user_id']
    name = request.form['name']
    type = request.form['type']
    balance = request.form['balance']
    currency = request.form['currency']
    creation_date = request.form['creation_date']
    last_update_date = request.form['last_update_date']

    # Validación básica de los datos
    if not name or not type or not balance or not currency or not creation_date or not last_update_date:
        flash('Please fill out all required fields', 'warning')
        return redirect(url_for('accounts'))

    # Intenta convertir la cantidad a un float
    try:
        balance = float(balance)
    except ValueError:
        flash('Invalid amount. Please enter a number.', 'danger')
        return redirect(url_for('accounts'))

    # Conectar a la base de datos
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
            INSERT INTO accounts (user_id, name, type, balance, currency, creation_date, last_update_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, name, type, balance, currency, creation_date, last_update_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
        flash('An error occurred while creating the account.', 'danger')
    finally:
        cur.close()
        conn.close()

    flash('Account created successfully!', 'success')
    return redirect(url_for('accounts'))


@app.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM accounts WHERE account_id = %s', (account_id,))
        conn.commit()
        flash('Account deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        print(e)
        flash('An error occurred while deleting the account.', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('accounts'))


#============================================================================Budgets===============================================================================================

@app.route('/budgets')
@login_required
def budgets():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM budgets WHERE user_id = %s', (user_id,))
    budget_data = cur.fetchall()

    # Obtiene las categorías
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()


    cur.close()
    conn.close()
    return render_template('budgets.html', budgets=budget_data, categories=categories)

@app.route('/create_budget', methods=['POST'])
@login_required
def create_budget():
    user_id = session['user_id']
    name = request.form['name']
    amount = request.form['amount']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    category = request.form['category']

    # Validación básica de los datos
    if not name or not amount or not start_date or not end_date or not category:
        flash('Please fill out all required fields', 'warning')
        return redirect(url_for('budgets'))

    # Intenta convertir la cantidad a un float
    try:
        amount = float(amount)
    except ValueError:
        flash('Invalid amount. Please enter a number.', 'danger')
        return redirect(url_for('budgets'))

    # Conectar a la base de datos
    conn = get_db_connection()
    cur = conn.cursor()

    print(user_id, name, amount, start_date, end_date, category)
    try:
        cur.execute('''
            INSERT INTO budgets (user_id, name, amount, start_date, end_date, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, name, amount, start_date, end_date, category))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
        flash('An error occurred while creating the budget.', 'danger')
    finally:
        cur.close()
        conn.close()

    flash('Budget created successfully!', 'success')
    return redirect(url_for('budgets'))


@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM budgets WHERE budget_id = %s', (budget_id,))
        conn.commit()
        flash('Budget deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('An error occurred while deleting the budget.', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('budgets'))


#============================================================================Transactions===============================================================================================

@app.route('/financial_goals')
@login_required
def financial_goals():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM financial_goals WHERE user_id = %s', (user_id,))

    financial_goal_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('financial_goals.html', financial_goals=financial_goal_data)

@app.route('/create_financial_goal', methods=['POST'])
@login_required
def create_financial_goal():
    user_id = session['user_id']
    name = request.form['name']
    description = request.form['description']
    target_amount = request.form['target_amount']
    saved_amount = request.form['saved_amount']
    due_date = request.form['due_date']

    # Validación básica de los datos
    if not name or not target_amount or not saved_amount or not due_date:
        flash('Please fill out all required fields', 'warning')
        return redirect(url_for('financial_goals'))

    # Intenta convertir la cantidad a un float
    try:
        target_amount = float(target_amount)
        saved_amount = float(saved_amount)
    except ValueError:
        flash('Invalid amount. Please enter a number.', 'danger')
        return redirect(url_for('financial_goals'))

    # Conectar a la base de datos
    conn = get_db_connection()
    cur = conn.cursor()

    print(user_id, name, description, target_amount, saved_amount, due_date)
    print(type(user_id), type(name), type(description), type(target_amount), type(saved_amount), type(due_date))
    # Insertar la nueva financial goals
    try:
        cur.execute('''
            INSERT INTO financial_goals (user_id, name, description, target_amount, saved_amount, due_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, name, description, target_amount, saved_amount, due_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
        flash('An error occurred while creating the financial goal.', 'danger')
    finally:
        cur.close()
        conn.close()

    flash('Financial goal created successfully!', 'success')
    return redirect(url_for('financial_goals'))


@app.route('/delete_financial_goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_financial_goal(goal_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM financial_goals WHERE goal_id = %s', (goal_id,))
        conn.commit()
        flash('Financial goal deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('An error occurred while deleting the financial goal.', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('financial_goals'))

#============================================================================Transactions===============================================================================================

@app.route('/transactions')
@login_required
def transactions():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Obtiene las transacciones
    cur.execute('SELECT * FROM transactions WHERE user_id = %s', (user_id,))
    transaction_data = cur.fetchall()

    # Obtiene las cuentas
    cur.execute('SELECT * FROM accounts WHERE user_id = %s', (user_id,))
    accounts = cur.fetchall()

    # Obtiene las categorías (Asumiendo que tienes una tabla para categorías)
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()

    # Consulta para obtener nombres de las cuentas
    cur.execute('SELECT account_id, name FROM accounts WHERE user_id = %s', (user_id,))
    account_names = {acc['account_id']: acc['name'] for acc in cur.fetchall()}


    cur.close()
    conn.close()

    return render_template('transactions.html', 
                           transactions=transaction_data, 
                           accounts=accounts, 
                           account_names=account_names, 
                           categories=categories)


@app.route('/create_transaction', methods=['POST'])
@login_required
def create_transaction():
    # Obtén los datos del formulario
    account_id = request.form['account_id']
    user_id = session['user_id']
    amount = request.form['amount']
    transaction_type = request.form['type']
    category = request.form['category']
    date = request.form['date']
    description = request.form['description']

    # Validación básica de los datos
    if not account_id or not amount or not transaction_type or not date:
        flash('Please fill out all required fields', 'warning')
        return redirect(url_for('transactions'))

    # Intenta convertir la cantidad a un float
    try:
        amount = float(amount)
    except ValueError:
        flash('Invalid amount. Please enter a number.', 'danger')
        return redirect(url_for('transactions'))

    # Conectar a la base de datos
    conn = get_db_connection()
    cur = conn.cursor()

    # Insertar la nueva transacción
    try:
        cur.execute('''
            INSERT INTO transactions (account_id, user_id, amount, type, category, date, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (account_id, user_id, amount, transaction_type, category, date, description))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash('An error occurred while creating the transaction.', 'danger')
    finally:
        cur.close()
        conn.close()

    flash('Transaction created successfully!', 'success')
    return redirect(url_for('transactions'))

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM transactions WHERE transaction_id = %s', (transaction_id,))
        conn.commit()
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('An error occurred while deleting the transaction.', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('transactions'))




if __name__ == '__main__':
    app.run()


