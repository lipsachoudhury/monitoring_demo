from flask import Blueprint, current_app, redirect, render_template, request, session, url_for, flash

from app.services.auth_service import verify_credentials

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if verify_credentials(username, password):
            session['logged_in'] = True
            session['username'] = current_app.config.get('ADMIN_USERNAME')
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
