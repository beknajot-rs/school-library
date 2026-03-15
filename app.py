from flask import Flask, render_template, request, redirect, url_for, flash
import database
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_library'

# Initialize database on startup module loading
try:
    database.init_db()
except Exception as e:
    print(f"Error initializing database: {e}")

@app.before_request
def setup_database_on_request():
    """Ensure database tables exist before handling any request in serverless."""
    try:
        database.init_db()
    except Exception as e:
        print(f"Serverless DB Init Error: {e}")


@app.route('/')
def dashboard():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    # Get total books sum
    c.execute('SELECT SUM(total_copies) FROM books')
    total_books = c.fetchone()[0] or 0
    
    # Get currently issued
    c.execute('SELECT COUNT(*) FROM loans WHERE status = "Faol" AND return_date IS NULL')
    res = c.fetchone()
    currently_issued = res[0] if res else 0
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    # Get issued today
    c.execute('SELECT COUNT(*) FROM loans WHERE issue_date = ?', (today_str,))
    res = c.fetchone()
    issued_today = res[0] if res else 0
    
    # Get returned today
    c.execute('SELECT COUNT(*) FROM loans WHERE return_date = ?', (today_str,))
    res = c.fetchone()
    returned_today = res[0] if res else 0
    
    # Get overdue
    c.execute('SELECT COUNT(*) FROM loans WHERE status = "Faol" AND due_date < ? AND return_date IS NULL', (today_str,))
    res = c.fetchone()
    overdue_count = res[0] if res else 0
    
    # Recent loans for table
    c.execute('''
        SELECT loans.id, students.full_name as student_name, books.title as book_title, 
               loans.issue_date, loans.due_date, loans.status
        FROM loans
        JOIN students ON loans.student_id = students.id
        JOIN books ON loans.book_id = books.id
        ORDER BY loans.issue_date DESC LIMIT 10
    ''')
    recent_loans = c.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                           title='Kutubxona boshqaruv paneli',
                           total_books=total_books,
                           currently_issued=currently_issued,
                           issued_today=issued_today,
                           returned_today=returned_today,
                           overdue_count=overdue_count,
                           recent_loans=recent_loans,
                           today_date_str=today_str)

@app.route('/books', methods=['GET', 'POST'])
def books():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        inventory_number = request.form['inventory_number']
        total_copies = request.form['total_copies']
        category = request.form.get('category', '')
        grade_level = request.form.get('grade_level', '')
        publisher = request.form.get('publisher', '')
        publish_year = request.form.get('publish_year', '')
        isbn = request.form.get('isbn', '')
        notes = request.form.get('notes', '')
        
        try:
            c.execute('''
                INSERT INTO books (inventory_number, title, author, category, grade_level, total_copies, publisher, publish_year, isbn, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (inventory_number, title, author, category, grade_level, total_copies, publisher, publish_year, isbn, notes))
            conn.commit()
            flash('Kitob muvaffaqiyatli qo\'shildi!', 'success')
        except sqlite3.IntegrityError:
            flash('Ushbu inventar raqamli kitob mavjud!', 'error')
        return redirect(url_for('books'))
        
    c.execute('SELECT * FROM books ORDER BY id DESC')
    all_books = c.fetchall()
    
    books_data = []
    for b in all_books:
        book_dict = dict(b)
        c.execute('SELECT COUNT(*) FROM loans WHERE book_id = ? AND status = "Faol" AND return_date IS NULL', (b['id'],))
        res = c.fetchone()
        issued_count = res[0] if res else 0
        book_dict['available_copies'] = book_dict['total_copies'] - issued_count
        books_data.append(book_dict)
        
    conn.close()
    return render_template('books.html', title='Kitoblar fondi', books=books_data)

@app.route('/delete_book/<int:id>', methods=['POST'])
def delete_book(id):
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Kitob o\'chirildi!', 'success')
    return redirect(url_for('books'))

@app.route('/students', methods=['GET', 'POST'])
def students():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        student_id = request.form['student_id']
        grade_level = request.form['grade_level']
        parent_phone = request.form.get('parent_phone', '')
        status = request.form.get('status', 'Faol')
        
        try:
            c.execute('''
                INSERT INTO students (student_id, full_name, grade_level, parent_phone, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, full_name, grade_level, parent_phone, status))
            conn.commit()
            flash('O\'quvchi muvaffaqiyatli qo\'shildi!', 'success')
        except sqlite3.IntegrityError:
            flash('Ushbu ID raqamli o\'quvchi mavjud!', 'error')
        return redirect(url_for('students'))
        
    c.execute('SELECT * FROM students ORDER BY id DESC')
    all_students = c.fetchall()
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    students_data = []
    for s in all_students:
        s_dict = dict(s)
        c.execute('SELECT COUNT(*) FROM loans WHERE student_id = ? AND status = "Faol" AND return_date IS NULL', (s['id'],))
        res1 = c.fetchone()
        s_dict['active_loans'] = res1[0] if res1 else 0
        
        c.execute('SELECT COUNT(*) FROM loans WHERE student_id = ? AND status = "Faol" AND due_date < ? AND return_date IS NULL', (s['id'], today_str))
        res2 = c.fetchone()
        s_dict['overdue_loans'] = res2[0] if res2 else 0
        
        students_data.append(s_dict)
        
    conn.close()
    return render_template('students.html', title="O'quvchilar", students=students_data)

@app.route('/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('O\'quvchi o\'chirildi!', 'success')
    return redirect(url_for('students'))

@app.route('/issue', methods=['GET', 'POST'])
def issue_book():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        book_id = request.form['book_id']
        due_date = request.form['due_date']
        issue_date = datetime.now().strftime('%Y-%m-%d')
        
        c.execute('''
            INSERT INTO loans (student_id, book_id, issue_date, due_date)
            VALUES (?, ?, ?, ?)
        ''', (student_id, book_id, issue_date, due_date))
        conn.commit()
        conn.close()
        flash('Kitob muvaffaqiyatli berildi!', 'success')
        return redirect(url_for('issue_book'))
        
    c.execute('SELECT id, full_name, student_id FROM students WHERE status = "Faol"')
    students = c.fetchall()
    
    c.execute('SELECT * FROM books')
    all_books = c.fetchall()
    available_books = []
    for b in all_books:
        b_dict = dict(b)
        c.execute('SELECT COUNT(*) FROM loans WHERE book_id = ? AND status = "Faol" AND return_date IS NULL', (b['id'],))
        issued = c.fetchone()[0]
        b_dict['available_copies'] = b_dict['total_copies'] - issued
        if b_dict['available_copies'] > 0:
            available_books.append(b_dict)
            
    conn.close()
    return render_template('issue.html', title='Kitob berish', students=students, books=available_books)

@app.route('/return')
def return_book():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    search_query = request.args.get('q', '')
    
    if search_query:
        c.execute('''
            SELECT loans.id, students.full_name as student_name, books.title as book_title, books.inventory_number,
                   loans.issue_date, loans.due_date
            FROM loans
            JOIN students ON loans.student_id = students.id
            JOIN books ON loans.book_id = books.id
            WHERE loans.status = "Faol" AND loans.return_date IS NULL
            AND (students.full_name LIKE ? OR books.title LIKE ? OR books.inventory_number LIKE ?)
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        active_loans = c.fetchall()
    else:
        c.execute('''
            SELECT loans.id, students.full_name as student_name, books.title as book_title, books.inventory_number,
                   loans.issue_date, loans.due_date
            FROM loans
            JOIN students ON loans.student_id = students.id
            JOIN books ON loans.book_id = books.id
            WHERE loans.status = "Faol" AND loans.return_date IS NULL
            ORDER BY loans.issue_date DESC LIMIT 50
        ''')
        active_loans = c.fetchall()
        
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.strptime(today_str, '%Y-%m-%d')
    
    loans_data = []
    for l in active_loans:
        l_dict = dict(l)
        due = datetime.strptime(l['due_date'], '%Y-%m-%d')
        diff = (today_date - due).days
        l_dict['delay_days'] = diff if diff > 0 else 0
        loans_data.append(l_dict)
        
    conn.close()
    return render_template('return.html', title='Kitob qabul qilish', loans=loans_data, search_query=search_query)

@app.route('/process_return/<int:loan_id>', methods=['POST'])
def process_return(loan_id):
    condition = request.form.get('condition', 'Yaxshi')
    return_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE loans 
        SET status = "Yakunlandi", return_date = ?, returned_condition = ?
        WHERE id = ?
    ''', (return_date, condition, loan_id))
    conn.commit()
    conn.close()
    
    flash('Kitob muvaffaqiyatli qabul qilindi!', 'success')
    return redirect(url_for('return_book'))

@app.route('/overdue')
def overdue():
    return render_template('overdue.html', title="Muddati o'tgan ijaralar")

@app.route('/reports')
def reports():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    # Top 10 books
    c.execute('''
        SELECT books.title, books.inventory_number, COUNT(loans.id) as borrow_count
        FROM loans
        JOIN books ON loans.book_id = books.id
        GROUP BY books.id
        ORDER BY borrow_count DESC
        LIMIT 10
    ''')
    top_books = c.fetchall()
    
    # Top 10 students
    c.execute('''
        SELECT students.full_name, students.grade_level, COUNT(loans.id) as read_count
        FROM loans
        JOIN students ON loans.student_id = students.id
        GROUP BY students.id
        ORDER BY read_count DESC
        LIMIT 10
    ''')
    top_students = c.fetchall()
    
    conn.close()
    return render_template('reports.html', title='Hisobotlar va statistika', top_books=top_books, top_students=top_students)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        school_name = request.form.get('school_name', '')
        school_address = request.form.get('school_address', '')
        principal_name = request.form.get('principal_name', '')
        standard_loan_days = request.form.get('standard_loan_days', 14)
        
        c.execute('''
            UPDATE settings
            SET school_name = ?, school_address = ?, principal_name = ?, standard_loan_days = ?
            WHERE id = 1
        ''', (school_name, school_address, principal_name, standard_loan_days))
        conn.commit()
        flash('Sozlamalar saqlandi!', 'success')
        return redirect(url_for('settings'))
        
    c.execute('SELECT * FROM settings WHERE id = 1')
    setting = c.fetchone()
    conn.close()
    
    return render_template('settings.html', title='Sozlamalar', setting=setting)

@app.context_processor
def inject_settings():
    try:
        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM settings WHERE id = 1')
        setting = c.fetchone()
        conn.close()
        return dict(system_settings=setting if setting else {})
    except Exception as e:
        print(f"Context Processor Error: {e}")
        return dict(system_settings={})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
